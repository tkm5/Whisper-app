import os

from functions import AudioTranscriber
import discord_notification
import settings

AUDIO_FILE = 'tmp.mov'
audio_path = os.path.join(settings.AUDIO_DIR, AUDIO_FILE)
OUTPUT_FILE_NAME = AUDIO_FILE.split(".")[0]  # Do not need file extension

if __name__ == '__main__':
    transcriber = AudioTranscriber(
        model_name=settings.MODEL,
        lang=settings.LANG,
        use_api=False,
    )
    minutes_dict = transcriber.audio_to_text(audio_path)
    transcriber.write_to_text(f'{settings.OUTPUT_DIR}/{OUTPUT_FILE_NAME}.txt', minutes_dict)
    # transcriber.export_csv(f'./output/{OUTPUT_FILE_NAME}.csv', minutes_dict)
    discord_notification.post_notice(message=f'{OUTPUT_FILE_NAME} minutes is DONE! from RTX4090')