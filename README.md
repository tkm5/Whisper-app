# Whisper-app

## Overview

This application uses OpenAI's Whisper-API or a local model to output a meeting minutes.
The minutes are output in the following two formats.

1. csv

    | index | start_time | end_time | speach_text |
    | --- | --- | --- | --- |
    | 1 | 00:00:00 | 00:00:02 | We're all here. |
    | 2 | 00:00:02 | 00:00:08 | Today we discuss Whisper. |
    | 3 | 00:00:08 | 00:00:15 | Let's discuss the model. |
    | 4 | 00:00:15 | 00:00:33 | Large model will be the best system. |
    | 5 | 00:00:33 | 00:00:43 | But the capacity is large. |

2. text

    [00:00:00] --> [00:00:02] | We're all here.
    [00:00:02] --> [00:00:08] | Today we discuss Whisper.
    [00:00:08] --> [00:00:15] | Let's discuss the model.
    [00:00:15] --> [00:00:33] | Large model will be the best system.
    [00:00:33] --> [00:00:43] | But the capacity is large.

## Quick Start

### Common

1. Install the package.
    `$ pip install -r requirements.txt`
2. Setting up audio files.

    1. Save the file under `whisper-app/audio/`.

### Local environment

1. Install dependencies.

    1. Linux
        `$ sudo apt update && sudo apt install ffmpeg`
    2. MacOS
        `$ brew install ffmpeg`
        Additional Information
        The MacOS installation command requires **[Homebrew](https://brew.sh/?ref=assemblyai.com)**. The Windows installation command requires **[Chocolatey](https://chocolatey.org/install?ref=assemblyai.com)**. Install either tool as needed.
    3. Windows
        `$ chco install ffmpeg`
        Additional Information
        Finally, if you are using Windows, make sure that developer mode is enabled. In the system settings, go to **Privacy & Security > For Developers** and turn on developer mode by turning on the top toggle switch (if it is not already on).
2. Run `main.py`

### Docker environment

1. Enter the audio file name in `AUDIO_FILE` of `settings.py`.
2. Create `secret.py` and fill in the Discord Webhook URL in `web_hook_url`. If you use the API, you will also need to enter your OpenAI API Key in `openai_api_key`.

    ```python
    web_hook_url = '<input here>'
    openai_api_key = '<input here>'
    ```

3. Run docker-compose.
    `$ docker-compose up -d`

## To receive completion notifications on Discord

1. Refer to the following URL to obtain the Discord webhook URL.
    [Super Easy Python Discord Notifications (API and Webhook)](https://10mohi6.medium.com/super-easy-python-discord-notifications-api-and-webhook-9c2d85ffced9)
2. Create `secret.py` as follows.

    ```python
    web_hook_url = '<input here>'
    ```

3. Additional Information
    The discordwebhook package has already been downloaded in requirements.txt.
