# LivePhotoPost

ライブ撮影写真を X (Twitter) に自動投稿するツール。  
写真の EXIF 日時とカレンダーのイベント情報を照合し、公演名・会場名付きで投稿する。

## 処理フロー

```
PHOTO_DIR/
└── {被写体ID}/
    └── photo.jpg  ──(EXIF日時)──┐
                                  ├──► カレンダー検索 ──► イベント名 + チケットURL
CALENDAR (iCal URL) ─────────────┘                              │
                                                                 ▼
                                                         会場名取得 (venue_scraper)
                                                                 │
                                                                 ▼
                                                         X に投稿 (Tweepy)
```

1. `PHOTO_DIR` 配下の被写体別ディレクトリから写真を 1 枚ずつ取得し、EXIF で撮影日時を読む
2. Google カレンダー (iCal) から撮影日時に最も近い予定を検索し、公演名とチケット URL を取得する
3. チケット URL からドメイン別スクレイパーで会場名を取得する
4. X API で指定フォーマットの投稿を行う

## セットアップ

### uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、シェルを再起動するか `source ~/.bashrc` を実行してパスを反映する。

### Infisicalのインストール
```
curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo bash
sudo apt-get install infisical
infisical login
infisical init
```

### 依存パッケージのインストール

**開発環境（Docker）**

`.venv_docker` を使用する。`.claude/settings.json` と `~/.bashrc` に `UV_PROJECT_ENVIRONMENT=.venv_docker` が設定済みのため、そのまま実行できる。

```bash
uv sync
```

**本番環境**

`.venv` を使用する。`~/.bashrc` に環境変数を設定する。

```bash
echo 'export UV_PROJECT_ENVIRONMENT=.venv' >> ~/.bashrc
source ~/.bashrc
```

設定後は通常通り実行できる。

```bash
uv sync
```

### 環境変数の設定

`.env` ファイルをプロジェクトルートに作成する（`PHOTO_DIR` と `CALENDAR` のみ）。

```dotenv
# 写真データのルートディレクトリ（プロジェクト外のパスも可）
PHOTO_DIR=/path/to/photos

# Google カレンダーの iCal フィード URL（公開設定が必要）
CALENDAR=https://calendar.google.com/calendar/ical/...
```

X (Twitter) API 認証情報（`API_KEY`・`API_SECRET`・`ACCESS_TOKEN`・`ACCESS_TOKEN_SECRET`）は Infisical で管理する。`infisical init` 後、Infisical のプロジェクトにシークレットを登録すること。

### 投稿テンプレートの配置

`template/{被写体ID}.txt` を作成する。テンプレート内で使用できる変数は実装に準じる。

```
template/
├── actor_a.txt
└── actor_b.txt
```

## 実行

Infisical 経由でシークレットを注入して実行する。

```bash
./run.sh
```

内部では以下のコマンドを実行している。

```bash
infisical run -- uv run python -m src.main
```

## モジュール構成

| ファイル | 役割 | 状態 |
| --- | --- | --- |
| `src/venue_scraper.py` | チケット URL から会場名を取得 | 実装済み |
| `src/photo_loader.py` | `PHOTO_DIR` のスキャン・EXIF 日時取得 | 実装済み |
| `src/calendar_client.py` | iCal フェッチ・撮影日時に近いイベント検索 | 実装済み |
| `src/x_poster.py` | Tweepy を使った X への投稿 | 実装済み |
| `src/main.py` | エントリーポイント・モジュール統合 | 実装済み |

## 対応チケットサイト

`venue_scraper` が会場名を自動取得できるサイト一覧。

| ドメイン | 取得方式 |
| --- | --- |
| `t.livepocket.jp` | HTML regex (`[会場]` パターン) |
| `livepocket.jp` | HTML regex (`event-detail-info__place`) |
| `tiget.net` | HTML regex (meta description 内 `会場：`) |
| `ticketdive.com` | HTML regex (`>会場</span>` 直後) |
| `ticketvillage.jp` | HTML regex (`■ 会場` パターン) |
| `paylove.org` | REST API (`/api/events/{id}`) |
| その他 | 未対応 → `None` を返す |

詳細は [docs/venue-scraper.md](docs/venue-scraper.md) を参照。

## ディレクトリ構成

```
LivePhotoPost/
├── src/                  # アプリケーションソース
├── docs/                 # 仕様・設計ドキュメント
│   ├── spec-base.md      # 基本仕様
│   ├── venue-scraper.md  # venue_scraper 仕様
│   └── structure.md      # ディレクトリ構成
├── template/             # 被写体別の投稿テンプレート
├── .env                  # 環境変数（Git 管理外）
└── CLAUDE.md             # Claude Code 向けプロジェクトガイド
```

## 技術スタック

| 用途 | ライブラリ |
| --- | --- |
| X 投稿 | Tweepy |
| 画像・EXIF | Pillow |
| HTTP クライアント | httpx |
| カレンダー取得 | icalendar, python-dateutil |
| 環境変数管理 | python-dotenv / Infisical CLI |
