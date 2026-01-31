# Whisper App

音声ファイルから会議議事録を生成するアプリケーション．

OpenAIのWhisperモデル（ローカル実行），Whisper API（クラウド），またはNVIDIA NIM Whisper（GPU高速処理）を使用して，音声をテキストに変換します．

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    docker compose                        │
├─────────────────┬───────────────────────────────────────┤
│  whisper-app    │  NIM Whisper (GPU環境のみ)             │
│  (クライアント)  │  nvcr.io/nim/nvidia/whisper-large-v3  │
│                 │  HTTP: 9000, gRPC: 50051              │
└─────────────────┴───────────────────────────────────────┘

[GPU環境] whisper-app → NIM API (localhost:9000)
[CPU環境] whisper-app → ローカルopenai-whisper (CPU)
```

## 出力形式

タイムスタンプ付きのテキストファイルを出力します．

```
[00:00:00] --> [00:00:02] | We are all here.
[00:00:02] --> [00:00:08] | Today we discuss Whisper.
[00:00:08] --> [00:00:15] | Let us discuss the model.
```

注意: NIM API使用時はセグメント情報（タイムスタンプ）が取得できないため，全体が1つのセグメントとして出力されます．

## 必要条件

- Python 3.10以上
- uv（パッケージマネージャ）
- FFmpeg
- CUDA対応GPU（推奨，CPUでも動作可能）
- NGC APIキー（NIM使用時）

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

### 2. uvのインストール

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Pythonパッケージのインストール

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

uv pip install .
```

### 4. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して必要な値を設定：

```bash
# 処理する音声ファイル（Docker使用時）
AUDIO_FILE=meeting.m4a

# NVIDIA NGC API Key（NIM使用時に必要）
NGC_API_KEY=your-ngc-api-key

# OpenAI API を使用する場合（--use-api オプション使用時に必要）
OPENAI_API_KEY=sk-your-api-key-here

# Discord通知を使用する場合（オプション）
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# Whisper設定（オプション，デフォルト値あり）
WHISPER_MODEL=large
WHISPER_LANG=ja

# NIMエンドポイント（Docker Compose内で自動設定）
NIM_ENDPOINT=http://nim-whisper:9000
```

### 5. NGC認証（NIM使用時）

```bash
# NGC APIキーを取得: https://org.ngc.nvidia.com/setup/api-key

# Dockerレジストリにログイン
docker login nvcr.io
# Username: $oauthtoken
# Password: <NGC_API_KEY>
```

### 6. 音声ファイルの配置

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
| `--nim` | NIM APIを強制使用 | False |
| `--no-notify` | Discord通知を無効化 | False |

### 使用例

```bash
# 日本語の会議を文字起こし（デフォルト設定）
python main.py meeting.m4a

# NIM APIを強制使用（GPU高速処理）
python main.py meeting.m4a --nim

# 英語の音声を中規模モデルで処理
python main.py interview.mp3 --model medium --lang en

# OpenAI APIを使用（クラウド処理）
python main.py meeting.m4a --use-api

# 通知なしで実行
python main.py meeting.m4a --no-notify

# ヘルプを表示
python main.py --help
```

## Docker での実行

### GPU環境（NIM使用）

NIMコンテナとwhisper-appを同時に起動します．

```bash
# 環境変数を設定
cp .env.example .env
vim .env  # NGC_API_KEY等を設定

# GPU profileで起動
AUDIO_FILE=meeting.m4a docker compose --profile gpu up
```

注意: NIMコンテナは初回起動時にモデルをダウンロードするため，最大30分かかる場合があります．

### CPU環境（ローカルWhisper）

NIMコンテナなしでwhisper-appのみ起動します．

```bash
AUDIO_FILE=meeting.m4a docker compose up whisper
```

### ワンライナーで実行

```bash
# GPU環境
AUDIO_FILE=meeting.m4a docker compose --profile gpu up

# CPU環境
AUDIO_FILE=meeting.m4a docker compose up whisper
```

### NIMを明示的に使用

```bash
docker compose run whisper python main.py meeting.m4a --nim
```

### 環境変数一覧（Docker用）

| 変数 | 説明 | 必須 |
|------|------|------|
| `AUDIO_FILE` | 処理する音声ファイル名 | Yes |
| `NGC_API_KEY` | NVIDIA NGC APIキー | NIM使用時 |
| `OPENAI_API_KEY` | OpenAI APIキー | --use-api時 |
| `DISCORD_WEBHOOK_URL` | Discord通知用URL | No |
| `WHISPER_MODEL` | モデル名（デフォルト: large） | No |
| `WHISPER_LANG` | 言語コード（デフォルト: ja） | No |
| `NIM_ENDPOINT` | NIMエンドポイントURL | No（自動設定） |

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
├── .dockerignore
├── .gitignore
├── compose.yaml        # Docker Compose設定
├── Dockerfile
├── pyproject.toml      # Python依存関係（uv用）
└── README.md
```

## 処理モードの自動選択

whisper-appは以下の優先順位で処理モードを自動選択します：

1. `--nim` オプション指定 → NIM API使用
2. `--use-api` オプション指定 → OpenAI API使用
3. NIMエンドポイントが利用可能 → NIM API使用（自動検出）
4. 上記以外 → ローカルWhisperモデル使用

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

## NIM Whisperについて

NVIDIA NIM Whisperは，GPU上で高速に文字起こしを実行できるコンテナ化されたWhisperモデルです．

### 特徴

- 高速処理（約54分の音声を約40秒で処理）
- GPU最適化
- OpenAI API互換のインターフェース

### 制限事項

- セグメント情報（タイムスタンプ）は取得できません
- m4a形式は直接サポートされないため，内部でwavに変換されます
- 初回起動時にモデルダウンロードが必要（最大30分）

### サポートされる音声形式

- WAV（推奨）
- MP3
- FLAC
- OGG

m4a等の他の形式は自動的にWAVに変換されます．

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

### NIMコンテナが起動しない

1. NGC認証を確認：
   ```bash
   docker login nvcr.io
   ```

2. NGC_API_KEYが設定されているか確認：
   ```bash
   cat .env | grep NGC_API_KEY
   ```

3. GPUが利用可能か確認：
   ```bash
   nvidia-smi
   ```

### NIMヘルスチェック

```bash
curl http://localhost:9000/v1/health/ready
```

正常な場合：
```json
{"object":"health.response","message":"ready","status":"ready"}
```

### ポート競合エラー

既存のNIMコンテナが起動している場合：
```bash
docker ps | grep nim
docker stop <container_id>
```
