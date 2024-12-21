FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
# Install ffmpeg
RUN apt update && \
    apt install -y ffmpeg

WORKDIR /app/src

CMD ["python", "main.py"]
