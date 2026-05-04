# 仕様: x_poster.py

## 概要
Tweepy を使って X (Twitter) に写真を投稿するモジュール。メディアアップロードに v1.1 API、ツイート送信に v2 API を使用する。

## クラス・データ構造

### `XPoster`
X への写真投稿を担当するクラス。

**コンストラクタ引数**

| 引数 | 型 | 説明 |
| --- | --- | --- |
| `apiClient` | `tweepy.API` | v1.1 API クライアント（メディアアップロード用） |
| `v2Client` | `tweepy.Client` | v2 Client（ツイート投稿用） |

## メソッド

### `buildText(templateText: str, event: Event, venue: str) -> str`
テンプレート文字列のプレースホルダーを置換して投稿テキストを生成する。

| プレースホルダー | 置換内容 |
| --- | --- |
| `{date}` | イベント開始日を `YYYY/MM/DD` 形式でフォーマット |
| `{event_name}` | カレンダーイベントのタイトル（`Event.summary`） |
| `{venue}` | 会場名 |

### `post(photo: Photo, event: Event, venue: str, templateText: str) -> str`
写真を X に投稿し、投稿後に写真ファイルを削除する。

1. `buildText` で投稿テキストを生成する
2. v1.1 API でメディアをアップロードする（`media_upload`）
3. v2 API でツイートを送信する（`create_tweet`）
4. 投稿成功後に写真ファイルを削除する（`photo.path.unlink()`）
5. 投稿されたツイートの ID を文字列で返す

- メディアアップロードまたはツイート送信に失敗した場合は例外を送出し、写真ファイルは削除されない

## ファクトリ関数

### `createXPosterFromEnv() -> XPoster`
環境変数（Infisical 経由）から認証情報を読み込んで `XPoster` インスタンスを生成する。

| 環境変数 | 内容 |
| --- | --- |
| `API_KEY` | X API キー |
| `API_SECRET` | X API シークレット |
| `ACCESS_TOKEN` | アクセストークン |
| `ACCESS_TOKEN_SECRET` | アクセストークンシークレット |

## 依存ライブラリ

| ライブラリ | 用途 |
| --- | --- |
| `tweepy` | X API v1.1 / v2 クライアント |
