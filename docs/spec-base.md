# 基本仕様

## 処理概要
Xにライブの写真をポストする。

## 処理フロー
1. データディレクトリから、被写体別に写真を1枚ずつ取得する。
   - 写真がなければスキップ
   - データディレクトリの下に被写体別にディレクトリがある。
   - 写真のEXIFから撮影日時を取得する。
2. カレンダーから撮影日時に近い予定のタイトルと会場を取得する。
   - カレンダーに入れてあるチケットURLから会場名を取得する。
   - 会場名が取得出来ない写真は、その写真をスキップディレクトリに移動して、`1.`に戻って次の写真で再試行する。
3. 投稿する写真が存在した場合は、XのAPIを使用して、テンプレートで写真を投稿する。
   - 投稿した写真は削除する。

## テンプレート
下記のテンプレートの記載を置き換える。
- `{date}` をカレンダーの予定の`日付` `YYYY/MM/DD` 形式
- `{event_name}` を カレンダーの予定の `タイトル`
- `{event venue}` を `会場名`

## モジュール構成

| モジュール | 概要 | 詳細 |
| --- | --- | --- |
| `src/calendar_client.py` | Google Calendar の iCal フィードを取得し、撮影日時に最も近いイベントを検索する | [spec-calendar_client.md](spec-calendar_client.md) |
| `src/photo_loader.py` | データディレクトリを再帰スキャンして JPG 写真を読み込み、EXIF の撮影日時を取得する | [spec-photo_loader.md](spec-photo_loader.md) |
| `src/venue_scraper.py` | チケットサイトの URL から会場名を取得する。ドメインに応じて HTML 正規表現または REST API を使い分ける | [spec-venue_scraper.md](spec-venue_scraper.md) |
| `src/x_poster.py` | Tweepy を使って X に写真を投稿する。メディアアップロードに v1.1 API、ツイート送信に v2 API を使用する | [spec-x_poster.md](spec-x_poster.md) |
