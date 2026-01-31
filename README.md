# Whisper App

音声ファイルから会議議事録を生成するアプリケーション．

OpenAIのWhisperモデル（ローカル実行）またはWhisper API（クラウド）を使用して，音声をテキストに変換します．

## 出力形式

タイムスタンプ付きのテキストファイルを出力します．

```
[00:00:00] --> [00:00:02] | We are all here.
[00:00:02] --> [00:00:08] | Today we discuss Whisper.
[00:00:08] --> [00:00:15] | Let us discuss the model.
```

## 必要条件

- Python 3.10以上
- FFmpeg
- CUDA対応GPU（推奨，CPUでも動作可能）

## セットアップ

### 1. FFmpegのインストール

```bash
# Linux
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

### 2. Pythonパッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して必要な値を設定：

```bash
# OpenAI API を使用する場合（--use-api オプション使用時に必要）
OPENAI_API_KEY=sk-your-api-key-here

# Discord通知を使用する場合（オプション）
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# Whisper設定（オプション，デフォルト値あり）
WHISPER_MODEL=large
WHISPER_LANG=ja
```

### 4. 音声ファイルの配置

音声ファイルを `audio_files/` ディレクトリに配置します．

```bash
cp your_audio.m4a audio_files/
```

## 使い方

### 基本的な使用法

```bash
cd src
python main.py <音声ファイル名>
```

例：
```bash
python main.py meeting_2024.m4a
```

出力は `output/meeting_2024.txt` に保存されます．

### コマンドラインオプション

```bash
python main.py <音声ファイル名> [オプション]
```

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--model` | Whisperモデル名（tiny, base, small, medium, large） | large |
| `--lang` | 言語コード（ja, en など） | ja |
| `--use-api` | OpenAI APIを使用（ローカルモデルの代わりに） | False |
| `--no-notify` | Discord通知を無効化 | False |

### 使用例

```bash
# 日本語の会議を文字起こし（デフォルト設定）
python main.py meeting.m4a

# 英語の音声を中規模モデルで処理
python main.py interview.mp3 --model medium --lang en

# OpenAI APIを使用（高速だが有料）
python main.py meeting.m4a --use-api

# 通知なしで実行
python main.py meeting.m4a --no-notify

# ヘルプを表示
python main.py --help
```

## ディレクトリ構成

```
whisper-app/
├── audio_files/        # 入力音声ファイル
├── output/             # 出力テキストファイル
├── src/
│   ├── main.py         # エントリーポイント
│   ├── transcriber.py  # 文字起こしロジック
│   ├── notification.py # Discord通知
│   └── settings.py     # 設定
├── .env.example        # 環境変数テンプレート
├── .gitignore
├── README.md
└── requirements.txt
```

## Discord通知

文字起こし完了時にDiscordへ通知を送信できます．

1. Discordで Webhook URL を取得  
   参考: [Discord Webhook の作成方法](https://support.discord.com/hc/ja/articles/228383668)

2. `.env` に Webhook URL を設定
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

3. 通知を無効にする場合は `--no-notify` オプションを使用

## Whisperモデルについて

| モデル | パラメータ数 | VRAM必要量 | 相対速度 |
|--------|-------------|-----------|---------|
| tiny   | 39M         | ~1GB      | ~32x    |
| base   | 74M         | ~1GB      | ~16x    |
| small  | 244M        | ~2GB      | ~6x     |
| medium | 769M        | ~5GB      | ~2x     |
| large  | 1550M       | ~10GB     | 1x      |

GPUメモリが不足する場合は，より小さいモデルを使用してください．

## トラブルシューティング

### CUDA out of memory エラー

より小さいモデルを使用：
```bash
python main.py meeting.m4a --model medium
```

### FFmpegが見つからない

FFmpegがインストールされ，PATHに含まれていることを確認：
```bash
ffmpeg -version
```

### OpenAI API エラー

`.env` ファイルに正しいAPIキーが設定されているか確認：
```bash
cat .env | grep OPENAI_API_KEY
```

## Docker での実行

### 環境変数を設定して実行

```bash
# .envファイルを作成
cp .env.example .env
# AUDIO_FILEに処理するファイル名を設定
vim .env

# 実行
docker compose up --build
```

### ワンライナーで実行

```bash
AUDIO_FILE=meeting.m4a docker compose up --build
```

### 環境変数一覧（Docker用）

| 変数 | 説明 | 必須 |
|------|------|------|
| `AUDIO_FILE` | 処理する音声ファイル名 | Yes |
| `OPENAI_API_KEY` | OpenAI APIキー | --use-api時 |
| `DISCORD_WEBHOOK_URL` | Discord通知用URL | No |
| `WHISPER_MODEL` | モデル名（デフォルト: large） | No |
| `WHISPER_LANG` | 言語コード（デフォルト: ja） | No |
