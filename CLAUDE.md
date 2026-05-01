# Project Guide: Live Photo Post
Xにライブの写真をポストする。

---

## プロジェクト構成

| レイヤー | 技術 |
| --- | --- |
| 投稿スクリプト | Python 3.13, Tweepy, python-dotenv |
| 画像処理・EXIF | Pillow |
| HTTP クライアント | httpx |
| カレンダー取得 | icalendar, python-dateutil |
| 会場名取得 | httpx + 正規表現 / REST API |

### モジュール構成

| ファイル | 役割 | 状態 |
| --- | --- | --- |
| `src/venue_scraper.py` | チケットURLから会場名を取得 | 実装済み |
| `src/photo_loader.py` | データディレクトリのスキャン・EXIF日時取得 | 未実装 |
| `src/calendar_client.py` | iCalフェッチ・撮影日時に近いイベント検索 | 未実装 |
| `src/x_poster.py` | Tweepy を使った X への投稿 | 未実装 |
| `src/main.py` | エントリーポイント・モジュール統合 | 未実装 |

### 環境変数

| 変数名 | 内容 |
| --- | --- |
| `PHOTO_DIR` | 写真データディレクトリのパス（プロジェクト外も指定可） |
| `CALENDAR` | Google Calendar の iCal フィード URL |
| `X_API_KEY` 等 | X (Twitter) API 認証情報 |

### 対応チケットサイト

| ドメイン | 取得方式 |
| --- | --- |
| `t.livepocket.jp` | HTML regex → Claude Haiku |
| `livepocket.jp` | HTML regex → Claude Haiku |
| `tiget.net` | HTML regex → Claude Haiku |
| `ticketdive.com` | HTML regex → Claude Haiku |
| `ticketvillage.jp` | HTML regex → Claude Haiku |
| `paylove.org` | REST API (`/api/events/{id}`) 直接取得 |
| その他 | HTML 本文テキスト → Claude Haiku |

詳細は [`docs/venue-scraper.md`](docs/venue-scraper.md) を参照。

---

## コーディング規約

- **命名規則**: メソッド名・変数名はキャメルケース（例: `userName`, `myFunction()`）
- **セキュリティ**: 認証情報はソースコードに直接記載しない（`.env` を使用）。画像配信時はパストラバーサル対策を必ず行う。
- **設計**: 依存性の注入（DI）で実装し、疎結合を保つ。
- **ドキュメント**: 全てのクラス・関数に Doc コメントを必ず記載する。
- **可読性**: 処理の意図が分かるよう、ロジックには適宜内部コメントを記載する。

---

## タスクガイダンス
- タスク実行時は `docs/tasks/*.md` にある指示書を最優先で確認すること。
- 作業完了
  - 指示書の TODO リストを更新する。
  - プロジェクト構成に更新があれば、プロジェクト構成を更新する。
    - 更新したら教えて下さい。

---

# 開発環境
- Dockerコンテナ上での開発であること留意すること
- ユニットテストは`.venv_docker`を使用すること
- `VSCode`の`Claude Code拡張`を使用している。

---

## 開発ワークフロー

**Research → Plan → Execute → Review → Ship** の順で進める。

1. **Research**: 既存実装・ライブラリを先に調査する（`gh search code`、Context7）
2. **Plan**: 必ずプランモードで開始。フェーズ分けしてゲート条件（テスト通過）を設ける
3. **Execute**: TDDで実装（テスト先行）
4. **Review**: `code-reviewer` エージェントで確認
5. **Ship**: ビルド確認後にコミット

---

## Claude Code セッション管理

- **新タスク = 新セッション** — 無関係なタスクは `/clear` でコンテキストを切り替える
- **コンテキスト 25% 到達で `/compact`** — 自動コンパクトより手動のほうが精度が高い
- **複数ファイルの調査はサブエージェントに委任** — 調査結果だけをメインコンテキストに返す
- **行き詰まったら `/rewind`** — 失敗した試みの前の状態に戻って再プロンプト

---

## Git 運用

- **1時間に1回、タスク完了時点でコミット**（後から squash merge する）
- **PRは小さく集中させる**（目安: 変更行数 p50 = 118行）
- 詳細は `.claude/rules/git.md` を参照

---
