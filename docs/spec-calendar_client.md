# 仕様: calendar_client.py

## 概要
Google Calendar の iCal フィードを取得し、写真の撮影日時に最も近いイベントを検索するモジュール。

## クラス・データ構造

### `Event` (dataclass)
カレンダーイベント情報を保持する。

| フィールド | 型 | 説明 |
| --- | --- | --- |
| `summary` | `str` | イベントのタイトル |
| `startAt` | `datetime` | イベント開始日時 |
| `url` | `Optional[str]` | チケットサイト等の URL。存在しない場合は `None` |

### `CalendarClient`
iCal フィードの取得・解析を行うクラス。

**コンストラクタ引数**

| 引数 | 型 | 説明 |
| --- | --- | --- |
| `calendarUrl` | `str` | Google Calendar の iCal フィード URL |
| `httpClient` | `Optional[httpx.Client]` | HTTP クライアント。省略時は `httpx.Client()` を自動生成 |

## メソッド

### `fetchEvents() -> list[Event]`
iCal フィードを HTTP で取得し、VEVENT コンポーネントをパースして `Event` リストを返す。

- `SUMMARY` または `DTSTART` が欠けているイベントはスキップする
- `URL` プロパティが存在する場合、`Event.url` に格納する
- HTTP エラー時は `httpx.HTTPError` を送出する

### `findNearestEvent(takenAt: datetime, events: list[Event]) -> Optional[Event]`
撮影日時 `takenAt` に対して開始日時の差が最小のイベントを返す。

- タイムゾーン付き `startAt` は naive datetime に変換して比較する
- `events` が空の場合は `None` を返す

## 依存ライブラリ

| ライブラリ | 用途 |
| --- | --- |
| `httpx` | iCal フィードの HTTP 取得 |
| `icalendar` | iCal データのパース |
