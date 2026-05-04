# 仕様: venue_scraper.py

## 概要
チケットサイトの URL から会場名を取得するモジュール。ドメインに応じて HTML 正規表現抽出または REST API を使い分ける。

## 関数

### `getVenue(ticketUrl: str) -> str | None`
チケット URL から会場名を取得するエントリーポイント。

- URL のドメインを解析し、対応する抽出処理にルーティングする
- 対応していないドメインの場合は `None` を返す
- HTML 取得や解析に失敗した場合も `None` を返す

## ドメイン別取得方式

| ドメイン | 取得方式 | 詳細 |
| --- | --- | --- |
| `paylove.org` | REST API | `/api/events/{id}` の `data.venue` フィールドを取得 |
| `t.livepocket.jp` | HTML 正規表現 | `[会場]会場名` パターンで抽出 |
| `livepocket.jp` | HTML 正規表現 | `event-detail-info__place` の `dd` テキストで抽出 |
| `tiget.net` | HTML 正規表現 | `meta description` 内の `会場：会場名` パターンで抽出 |
| `ticketdive.com` | HTML 正規表現 | 会場ラベル直後の `span` テキストで抽出 |
| `ticketvillage.jp` | HTML 正規表現 | `■ 会場　会場名` パターンで抽出 |
| その他 | 非対応 | `None` を返す |

## 内部実装

### HTML 取得 (`_fetchHtml`)
- `User-Agent` ヘッダーを付与してリクエストを送信する
- リダイレクトに追従する（`follow_redirects=True`）
- タイムアウト: 10 秒
- HTTP エラーまたは例外が発生した場合は `None` を返す

### paylove.org REST API 取得 (`_getVenuePaylove`)
- URL パスの末尾からイベント ID を抽出する
- `https://paylove.org/api/events/{id}` にリクエストを送信する
- レスポンス JSON の `data.venue` を返す

## 依存ライブラリ

| ライブラリ | 用途 |
| --- | --- |
| `httpx` | HTML / API の HTTP 取得 |
| `re` | HTML からの正規表現抽出 |
