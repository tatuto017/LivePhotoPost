# ディレクトリ構成

```
LivePhotoPost/
├── src/                          # アプリケーションソース
│   ├── venue_scraper.py          # チケットURLから会場名を取得
│   ├── photo_loader.py           # (未実装) データディレクトリスキャン・EXIF日時取得 ($PHOTO_DIR)
│   ├── calendar_client.py        # (未実装) iCalフェッチ・撮影日時に近いイベント検索
│   ├── x_poster.py               # (未実装) Tweepy を使った X への投稿
│   └── main.py                   # (未実装) エントリーポイント・モジュール統合
│
├── docs/                         # プロジェクトドキュメント
│   ├── spec-base.md              # 基本仕様書
│   ├── venue-scraper.md          # venue_scraper モジュール仕様
│   └── structure.md              # このファイル
│
├── template/                     # 投稿のテンプレート
│   ├── actor_a.txt               # 被写体別の投稿のテンプレート(被写体ID.txt)
│   └── actor_b.txt               # 被写体別の投稿のテンプレート(被写体ID.txt)
│
├── .claude/                      # Claude Code 設定
│   ├── rules/
│   │   └── git.md                # Git 運用ルール
│   └── settings.json             # Claude Code プロジェクト設定
│
├── .env                          # 環境変数 (Git 管理外)
├── .gitignore                    # Git 除外設定
├── .mcp.json                     # MCP サーバー設定
└── CLAUDE.md                     # プロジェクトガイド (Claude Code 向け)
```

### データディレクトリ（`PHOTO_DIR` で指定、`PROJECT_ROOT` 外に配置可能）
```text
{PHOTO_DIR}/                      # 環境変数 PHOTO_DIR で指定した任意のパス
├── actor_a/                      # 被写体別ディレクトリ(ディレクトリ名が被写体ID)
└── actor_b/                      # 被写体別ディレクトリ(ディレクトリ名が被写体ID)
```

## 主要ファイル説明

### src/

| ファイル | 役割 | 状態 |
| --- | --- | --- |
| `venue_scraper.py` | チケットURLからドメイン別に会場名を取得 | 実装済み |
| `photo_loader.py` | データディレクトリ（`$PHOTO_DIR`）のスキャン・EXIF日時取得 | 実装済み |
| `calendar_client.py` | Google Calendar の iCal フェッチ・イベント検索 | 実装済み |
| `x_poster.py` | Tweepy を使った X (Twitter) への投稿 | 実装済み |
| `main.py` | エントリーポイント・各モジュールの統合 | 実装済み |

### 設定ファイル

| ファイル | 用途 |
| --- | --- |
| `.env` | `CALENDAR`、`X_API_KEY` 等の認証情報（Git 管理外） |
| `.gitignore` | Git 除外ルール |
| `.mcp.json` | token-savior 等の MCP サーバー設定 |
| `CLAUDE.md` | Claude Code 向けプロジェクトガイド |

### docs/

| ファイル | 内容 |
| --- | --- |
| `spec-base.md` | プロジェクト基本仕様 |
| `venue-scraper.md` | `venue_scraper.py` の詳細仕様・対応ドメイン一覧 |
| `structure.md` | ディレクトリ構成（このファイル） |
