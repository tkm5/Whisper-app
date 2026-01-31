FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# システム依存関係インストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係をコピーしてインストール
COPY pyproject.toml .
RUN uv venv /app/.venv --python python3.12 \
    && . /app/.venv/bin/activate \
    && uv pip install .

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# アプリケーションコードをコピー
COPY src/ ./src/

WORKDIR /app/src

CMD ["python", "main.py"]
