"""アプリケーション設定モジュール．"""
import os
from pathlib import Path

MODEL = os.getenv("WHISPER_MODEL", "large")
LANG = os.getenv("WHISPER_LANG", "ja")

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "audio_files"
OUTPUT_DIR = BASE_DIR / "output"

PROMPT = """

"""
