"""音声文字起こしアプリケーションのエントリーポイント．"""
import argparse
import logging
import os
import sys
from pathlib import Path

import settings
from notification import send_discord_notification
from transcriber import AudioTranscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する．"""
    parser = argparse.ArgumentParser(description="音声ファイルを文字起こしする")
    parser.add_argument(
        "audio_file",
        nargs="?",
        default=os.getenv("AUDIO_FILE"),
        help="音声ファイル名（audio_filesディレクトリ内）．環境変数AUDIO_FILEでも指定可能",
    )
    parser.add_argument("--model", default=settings.MODEL, help="Whisperモデル名")
    parser.add_argument("--lang", default=settings.LANG, help="言語コード")
    parser.add_argument("--use-api", action="store_true", help="OpenAI APIを使用")
    parser.add_argument("--nim", action="store_true", help="NIM APIを強制使用")
    parser.add_argument("--no-notify", action="store_true", help="Discord通知を無効化")
    return parser.parse_args()


def main() -> int:
    """メイン処理．"""
    args = parse_args()

    if not args.audio_file:
        logger.error("audio_file is required. Set via argument or AUDIO_FILE env var.")
        return 1

    audio_path = settings.AUDIO_DIR / args.audio_file
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return 1

    output_name = Path(args.audio_file).stem
    output_path = settings.OUTPUT_DIR / f"{output_name}.txt"

    logger.info(f"Transcribing: {audio_path}")

    try:
        transcriber = AudioTranscriber(
            model_name=args.model,
            lang=args.lang,
            use_api=args.use_api,
            use_nim=args.nim,
        )
        segments = transcriber.transcribe(audio_path)
        transcriber.write_to_text(output_path, segments)
        logger.info(f"Output written to: {output_path}")

        if not args.no_notify:
            send_discord_notification(f"{output_name} minutes is DONE! from H100")

        return 0
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
