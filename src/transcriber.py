"""音声文字起こしモジュール．"""
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict

import requests
import torch
import whisper
from openai import OpenAI

import settings

logger = logging.getLogger(__name__)


class TranscriptSegment(TypedDict):
    """文字起こしセグメントの型定義．"""

    start_time: str
    end_time: str
    text: str


class AudioTranscriber:
    """音声ファイルをテキストに変換するクラス．"""

    # NIM APIがサポートする音声形式
    NIM_SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".ogg"}

    def __init__(
        self,
        model_name: str = settings.MODEL,
        lang: str = settings.LANG,
        use_api: bool = False,
        use_nim: bool = False,
        device: str | None = None,
    ) -> None:
        """AudioTranscriberを初期化する．

        Args:
            model_name: 使用するWhisperモデル名．
            lang: 文字起こしの言語．
            use_api: OpenAI APIを使用するかどうか．
            use_nim: NIM APIを強制使用するかどうか．
            device: モデルをロードするデバイス．
        """
        self.prompt = settings.PROMPT
        self.lang = lang
        self.use_api = use_api
        self.use_nim = use_nim
        self.nim_endpoint = os.getenv("NIM_ENDPOINT", "http://localhost:9000")
        self.model = None

        api_key = os.getenv("OPENAI_API_KEY")
        if use_api and not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when use_api=True"
            )
        self.client = OpenAI(api_key=api_key) if api_key else None

        # NIMモード判定（自動検出）
        if not self.use_nim and self._is_nim_available():
            logger.info("NIM endpoint detected, using NIM API")
            self.use_nim = True

        # NIM使用時はローカルモデルをロードしない
        if not self.use_nim and not self.use_api:
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading local Whisper model on {device}")
            self.model = whisper.load_model(model_name, device=device)

    def _is_nim_available(self) -> bool:
        """NIMエンドポイントが利用可能か確認する．

        Returns:
            NIMエンドポイントが利用可能な場合True．
        """
        try:
            resp = requests.get(
                f"{self.nim_endpoint}/v1/health/ready",
                timeout=5,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def _convert_to_wav(self, audio_path: Path) -> Path:
        """音声ファイルをWAV形式に変換する．

        Args:
            audio_path: 変換元の音声ファイルパス．

        Returns:
            変換後のWAVファイルパス．

        Raises:
            RuntimeError: ffmpegによる変換に失敗した場合．
        """
        if audio_path.suffix.lower() in self.NIM_SUPPORTED_FORMATS:
            return audio_path

        logger.info(f"Converting {audio_path.suffix} to WAV format")

        # 一時ファイルとして変換後のWAVを作成
        temp_dir = Path(tempfile.gettempdir())
        wav_path = temp_dir / f"{audio_path.stem}_converted.wav"

        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(wav_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Converted to: {wav_path}")
            return wav_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to convert audio: {e.stderr}") from e

    @staticmethod
    def _format_time(seconds: float) -> str:
        """秒数をhh:mm:ss形式に変換する．"""
        total_seconds = int(seconds + 0.5)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"

    def transcribe(self, audio_path: str | Path) -> list[TranscriptSegment]:
        """音声ファイルを文字起こしする．

        Args:
            audio_path: 音声ファイルのパス．

        Returns:
            文字起こし結果のセグメントリスト．
        """
        audio_path = Path(audio_path)

        if self.use_nim:
            return self._transcribe_with_nim(audio_path)

        if self.use_api:
            return self._transcribe_with_openai_api(audio_path)

        return self._transcribe_with_local_model(audio_path)

    def _transcribe_with_nim(self, audio_path: Path) -> list[TranscriptSegment]:
        """NIM APIを使用した文字起こし．

        NIM APIはセグメント情報（タイムスタンプ）を返さないため，
        全体を1つのセグメントとして返す．

        Args:
            audio_path: 音声ファイルのパス．

        Returns:
            文字起こし結果のセグメントリスト．
        """
        logger.info(f"Transcribing with NIM API: {audio_path}")

        # 必要に応じてWAV形式に変換
        converted_path = self._convert_to_wav(audio_path)
        cleanup_converted = converted_path != audio_path

        try:
            url = f"{self.nim_endpoint}/v1/audio/transcriptions"

            with open(converted_path, "rb") as audio_file:
                files = {"file": (converted_path.name, audio_file, "audio/wav")}
                data = {
                    "language": self.lang,
                    "response_format": "json",
                }
                if self.prompt:
                    data["prompt"] = self.prompt

                response = requests.post(url, files=files, data=data, timeout=600)
                response.raise_for_status()
                result = response.json()

            # NIM APIはセグメント情報を返さないため，全体を1つのセグメントとして扱う
            text = result.get("text", "")
            return [
                TranscriptSegment(
                    start_time="00:00:00",
                    end_time="--:--:--",
                    text=text,
                )
            ]
        finally:
            # 変換した一時ファイルを削除
            if cleanup_converted and converted_path.exists():
                converted_path.unlink()

    def _transcribe_with_openai_api(self, audio_path: Path) -> list[TranscriptSegment]:
        """OpenAI APIを使用した文字起こし．

        Args:
            audio_path: 音声ファイルのパス．

        Returns:
            文字起こし結果のセグメントリスト．
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        logger.info(f"Transcribing with OpenAI API: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            result = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                language=self.lang,
                prompt=self.prompt,
            )

        segments = result.segments
        return [
            TranscriptSegment(
                start_time=self._format_time(seg.start),
                end_time=self._format_time(seg.end),
                text=seg.text,
            )
            for seg in segments
        ]

    def _transcribe_with_local_model(
        self, audio_path: Path
    ) -> list[TranscriptSegment]:
        """ローカルWhisperモデルを使用した文字起こし．

        Args:
            audio_path: 音声ファイルのパス．

        Returns:
            文字起こし結果のセグメントリスト．
        """
        if not self.model:
            raise ValueError("Local Whisper model not loaded")

        logger.info(f"Transcribing with local model: {audio_path}")

        result = self.model.transcribe(
            audio=str(audio_path),
            verbose=True,
            language=self.lang,
            prompt=self.prompt,
        )

        return [
            TranscriptSegment(
                start_time=self._format_time(seg["start"]),
                end_time=self._format_time(seg["end"]),
                text=seg["text"],
            )
            for seg in result["segments"]
        ]

    @staticmethod
    def write_to_text(
        output_path: str | Path, segments: list[TranscriptSegment]
    ) -> None:
        """文字起こし結果をテキストファイルに書き込む．

        Args:
            output_path: 出力ファイルのパス．
            segments: 文字起こしセグメントのリスト．
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                f.write(
                    f"[{seg['start_time']}] --> [{seg['end_time']}] | {seg['text']}\n"
                )
