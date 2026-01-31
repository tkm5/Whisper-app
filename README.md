# Whisper Web

音声ファイルの文字起こしを行う Web アプリケーション．

NVIDIA NIM Whisper を使用して GPU で高速に音声をテキストに変換します．ドラッグ＆ドロップで簡単にファイルをアップロードでき，結果のコピーやダウンロードが可能です．

## 機能

- Web UI でドラッグ＆ドロップによる音声ファイルアップロード
- NVIDIA NIM Whisper による高速文字起こし（GPU）
- 長時間音声の自動分割処理（25秒チャンク）
- 結果のクリップボードコピー・ダウンロード
- CLI による文字起こしも対応

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      docker compose                          │
├─────────────────────────┬───────────────────────────────────┤
│  whisper-web            │  nim-whisper (GPU)                 │
│  FastAPI + htmx         │  nvcr.io/nim/nvidia/whisper-large-v3│
│  Port: 8000             │  HTTP: 9000, gRPC: 50051           │
└─────────────────────────┴───────────────────────────────────┘

ブラウザ → whisper-web:8000 → nim-whisper:9000 (NIM API)
```

## クイックスタート

### 1. 環境変数の設定

```bash
cp .env.example .env
vim .env  # NGC_API_KEY を設定
```

### 2. NGC 認証

```bash
# NGC API キーを取得: https://org.ngc.nvidia.com/setup/api-key
docker login nvcr.io
# Username: $oauthtoken
# Password: <NGC_API_KEY>
```

### 3. 起動

```bash
# Web アプリ + NIM を起動（GPU 環境）
docker compose --profile gpu up -d

# ログを確認
docker compose logs -f
```

### 4. アクセス

ブラウザで以下にアクセス：

- ローカル: http://localhost:8000
- Tailscale 経由: http://h100-jaist:8000 または http://100.73.97.97:8000

## 起動コマンド

### Web アプリケーション（推奨）

```bash
# NIM + Web アプリを起動
docker compose --profile gpu up -d

# Web アプリのみ起動（NIM が既に起動している場合）
docker compose up -d whisper-web

# 停止
docker compose --profile gpu down
```

### CLI（コマンドライン）

```bash
# CLI で文字起こし
AUDIO_FILE=meeting.m4a docker compose --profile gpu --profile cli up whisper-cli
```

### サービス状態確認

```bash
# コンテナ状態を確認
docker compose ps

# NIM ヘルスチェック
curl http://localhost:9000/v1/health/ready
```

## Docker Compose サービス

| サービス | 説明 | ポート | プロファイル |
|----------|------|--------|-------------|
| nim-whisper | NVIDIA NIM Whisper API | 9000, 50051 | gpu |
| whisper-web | Web アプリケーション | 8000 | (default) |
| whisper-cli | CLI ツール | - | cli |

## 環境変数

| 変数 | 説明 | 必須 |
|------|------|------|
| NGC_API_KEY | NVIDIA NGC API キー | Yes（NIM 使用時） |
| AUDIO_FILE | CLI で処理する音声ファイル名 | CLI 使用時 |
| WHISPER_MODEL | モデル名（デフォルト: large） | No |
| WHISPER_LANG | 言語コード（デフォルト: ja） | No |
| OPENAI_API_KEY | OpenAI API キー | No |
| DISCORD_WEBHOOK_URL | Discord 通知用 URL | No |

## ディレクトリ構成

```
whisper-app/
├── audio_files/          # 入力音声ファイル
├── output/               # 出力テキストファイル
├── src/
│   ├── app.py            # FastAPI Web アプリ
│   ├── main.py           # CLI エントリーポイント
│   ├── transcriber.py    # 文字起こしロジック（チャンク分割対応）
│   ├── job_manager.py    # ジョブ管理
│   ├── notification.py   # Discord 通知
│   ├── settings.py       # 設定
│   └── templates/        # HTML テンプレート（htmx）
│       ├── index.html
│       └── partials/
│           ├── progress.html
│           ├── result.html
│           └── error.html
├── .env.example          # 環境変数テンプレート
├── compose.yaml          # Docker Compose 設定
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 出力形式

タイムスタンプ付きのテキストファイルを出力します．

```
[00:00:00] --> [00:00:25] | 最初のチャンクのテキスト...
[00:00:25] --> [00:00:50] | 次のチャンクのテキスト...
```

## 技術詳細

### 音声チャンク分割

NIM Whisper API は約30秒までの音声に対応しているため，長時間の音声ファイルは25秒ごとに自動分割して処理されます．

### サポートされる音声形式

- WAV（推奨）
- MP3
- M4A（内部で WAV に変換）
- FLAC
- OGG

### NIM について

NVIDIA NIM Whisper は GPU 上で高速に文字起こしを実行するコンテナ化された Whisper モデルです．

- 初回起動時にモデルダウンロード（最大30分）
- ヘルスチェックで起動完了を確認
- OpenAI API 互換のインターフェース

## トラブルシューティング

### NIM コンテナが起動しない

```bash
# GPU が利用可能か確認
nvidia-smi

# NGC 認証を確認
docker login nvcr.io

# ログを確認
docker compose logs nim-whisper
```

### ディスク容量不足

```bash
# Docker のキャッシュをクリア
docker system prune -a -f --volumes
```

### Web アプリに接続できない

```bash
# コンテナが起動しているか確認
docker compose ps

# ポートが開いているか確認
curl http://localhost:8000
```

### Tailscale 経由で接続できない

```bash
# Tailscale コンテナを起動
cd ~/tailscale
docker compose up -d

# Tailscale の状態を確認
docker exec tailscale tailscale status
```

## ライセンス

MIT License
