FROM python:3.12-slim

WORKDIR /app

ADD requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt && \
    apt update && \
    apt install -y ffmpeg

ADD . /app
