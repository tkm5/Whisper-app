from openai import OpenAI
import torch
import whisper
import pandas as pd

import secret
import settings


class AudioTranscriber:
    """A class for transcribing audio files to text.

    Attributes:
        model (whisper.Model): An instance of the Whisper model.
        lang (str): Language to use for transcription.
    """

    def __init__(self, model_name: str, lang: str, use_api: bool = True, device: str = None):
        """Initializes the AudioTranscriber class with a specific Whisper model and language.

        Args:
            model_name (str): Name of the Whisper model to be used.
            lang (str): Language to be used for transcription.
            device (str): Device to load the model on.
        """
        self.prompt = settings.PROMPT
        self.client = OpenAI(api_key=secret.openai_api_key)

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            # elif torch.backends.mps.is_available():
            #     device = "mps"
            else:
                device = "cpu"

        self.model = whisper.load_model(model_name, device=device)
        self.lang = lang
        self.use_api = use_api

    @staticmethod
    def elapsed_time_str(seconds: float) -> str:
        """Converts elapsed time in seconds to a formatted string (hh:mm:ss).

        Args:
            seconds (float): Elapsed time in seconds.

        Returns:
            str: Formatted time string in hh:mm:ss format.
        """
        seconds = int(seconds + 0.5)
        h = seconds // 3600
        m = (seconds - h * 3600) // 60
        s = seconds - h * 3600 - m * 60
        return f"{h:02}:{m:02}:{s:02}"

    def generate_minutes_dict(self, result: list) -> dict:
        """Generates a dictionary with start times, end times, and transcribed text from the results.

        Args:
            result (list): List of transcription results.

        Returns:
            dict: Dictionary containing start times, end times, and speech text.
        """
        if self.use_api:
            return {
                'start_time': [segment.start for segment in result],
                'end_time': [segment.end for segment in result],
                'speach_text': [segment.text for segment in result]
            }
        else:
            return {
                'start_time': [segment['start'] for segment in result],
                'end_time': [segment['end'] for segment in result],
                'speach_text': [segment['text'] for segment in result]
            }

    @staticmethod
    def write_to_text(text_path: str, minutes_dict: dict):
        """Writes the transcription results to a text file.

        Args:
            text_path (str): Path to the output text file.
            minutes_dict (dict): Dictionary of transcription results per minute.
        """
        with open(text_path, "w") as f:
            for i in range(len(minutes_dict["speach_text"])):
                print(
                    f'[{minutes_dict["start_time"][i]}] --> '
                    f'[{minutes_dict["end_time"][i]}] | '
                    f'{minutes_dict["speach_text"][i]}',
                    file=f
                )

    @staticmethod
    def export_csv(output_path: str, minutes_dict: dict):
        """Exports the transcription results to a CSV file.

        Args:
            output_path (str): Path to the output CSV file.
            minutes_dict (dict): Dictionary of transcription results per minute.
        """
        df = pd.DataFrame(minutes_dict)
        df.to_csv(output_path)

    def audio_to_text(self, audio_path: str) -> dict:
        """Transcribes an audio file to text.

        Args:
            audio_path (str): Path to the audio file to be transcribed.

        Returns:
            dict: Dictionary containing the transcription results.
        """
        if self.use_api:
            audio = open(audio_path, "rb")
            result_dict = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="verbose_json",
                language=self.lang,
                prompt=self.prompt,
            )
            result_dict = dict(result_dict)
        else:
            result_dict = self.model.transcribe(
                audio=audio_path,
                verbose=True,
                language=self.lang,
                prompt=self.prompt,
            )
        minutes_dict = self.generate_minutes_dict(result_dict['segments'])
        minutes_dict['start_time'] = [self.elapsed_time_str(t) for t in minutes_dict['start_time']]
        minutes_dict['end_time'] = [self.elapsed_time_str(t) for t in minutes_dict['end_time']]
        return minutes_dict
