"""音声文字起こしモジュール．"""
import os
from pathlib import Path
from typing import TypedDict

import torch
import whisper
from openai import OpenAI

import settings


class TranscriptSegment(TypedDict):
    """文字起こしセグメントの型定義．"""
    start_time: str
    end_time: str
    text: str


class AudioTranscriber:
    """音声ファイルをテキストに変換するクラス．"""

    def __init__(
        self,
        model_name: str = settings.MODEL,
        lang: str = settings.LANG,
        use_api: bool = False,
        device: str | None = None,
    ) -> None:
        """AudioTranscriberを初期化する．

        Args:
            model_name: 使用するWhisperモデル名．
            lang: 文字起こしの言語．
            use_api: OpenAI APIを使用するかどうか．
            device: モデルをロードするデバイス．
        """
        self.prompt = settings.PROMPT
        self.lang = lang
        self.use_api = use_api

        api_key = os.getenv("OPENAI_API_KEY")
        if use_api and not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required when use_api=True")
        self.client = OpenAI(api_key=api_key) if api_key else None

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = whisper.load_model(model_name, device=device)

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

        if self.use_api:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
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
        else:
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
    def write_to_text(output_path: str | Path, segments: list[TranscriptSegment]) -> None:
        """文字起こし結果をテキストファイルに書き込む．"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                f.write(f"[{seg['start_time']}] --> [{seg['end_time']}] | {seg['text']}\n")
