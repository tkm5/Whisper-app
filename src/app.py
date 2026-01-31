"""FastAPI Webアプリケーション．"""
import logging
import tempfile
from pathlib import Path

import aiofiles
from fastapi import FastAPI, Request, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from job_manager import JobManager, JobStatus
from transcriber import AudioTranscriber
import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Web")

# テンプレートとスタティックファイルの設定
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# ジョブ管理（インメモリ）
job_manager = JobManager()

# 一時ファイル保存ディレクトリ
UPLOAD_DIR = Path(tempfile.gettempdir()) / "whisper-uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """メインページを表示する．"""
    return templates.TemplateResponse(request, "index.html")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile) -> HTMLResponse:
    """音声ファイルをアップロードする．

    Args:
        request: FastAPIリクエスト．
        file: アップロードされたファイル．

    Returns:
        進捗表示のHTMLパーシャル．
    """
    job_id = job_manager.create_job(file.filename or "unknown")

    # ファイルを保存
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    job_manager.set_file_path(job_id, str(file_path))
    job_manager.update_status(job_id, JobStatus.PROCESSING)

    return templates.TemplateResponse(
        request,
        "partials/progress.html",
        {
            "job_id": job_id,
            "filename": file.filename,
            "status": "文字起こし中...",
        },
    )


@app.post("/transcribe/{job_id}", response_class=HTMLResponse)
async def transcribe(request: Request, job_id: str) -> HTMLResponse:
    """文字起こしを実行する．

    Args:
        request: FastAPIリクエスト．
        job_id: ジョブID．

    Returns:
        結果表示のHTMLパーシャル．
    """
    try:
        job = job_manager.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = Path(job.get("file_path", ""))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # 文字起こし実行
        transcriber = AudioTranscriber(
            model_name=settings.MODEL,
            lang=settings.LANG,
            use_nim=True,
        )
        segments = transcriber.transcribe(file_path)

        # 結果をテキストに変換
        result_text = ""
        for seg in segments:
            if seg["end_time"] == "--:--:--":
                result_text += f"{seg['text']}\n"
            else:
                result_text += f"[{seg['start_time']}] --> [{seg['end_time']}] | {seg['text']}\n"

        # 結果ファイルを保存
        output_path = settings.OUTPUT_DIR / f"{job_id}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_text)

        job_manager.set_result(job_id, result_text, str(output_path))

        return templates.TemplateResponse(
            request,
            "partials/result.html",
            {
                "job_id": job_id,
                "filename": job["filename"],
                "text": result_text,
            },
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        job_manager.update_status(job_id, JobStatus.FAILED)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "job_id": job_id,
                "filename": job["filename"],
                "error": str(e),
            },
        )


@app.get("/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    """結果ファイルをダウンロードする．

    Args:
        job_id: ジョブID．

    Returns:
        結果ファイル．
    """
    try:
        job = job_manager.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    result_path = job.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        result_path,
        media_type="text/plain",
        filename=f"{Path(job['filename']).stem}.txt",
    )
