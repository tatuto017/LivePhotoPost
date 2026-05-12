# venue_scraper モジュール設計ドキュメント

## 概要

`src/venue_scraper.py` — チケットサイトのURLから会場名を取得するモジュール。  
AIは使用せず、ドメイン別の正規表現と REST API のみで会場名を抽出する。  
未対応ドメインは `None` を返す。

---

## 対応ドメインと取得方式

| ドメイン | 方式 | 抽出パターン |
|---|---|---|
| `t.livepocket.jp` | HTML regex | `[会場]会場名` パターン |
| `livepocket.jp` | HTML regex | `event-detail-info__place` の `<dd>` テキスト |
| `tiget.net` | HTML regex | meta description 内の `会場：会場名` |
| `ticketdive.com` | HTML regex | `>会場</span><span>会場名` |
| `ticketvillage.jp` | HTML regex | `■ 会場　会場名` パターン |
| `paylove.org` | REST API | `GET /api/events/{id}` の `data.venue` フィールド |
| その他 | — | `None` を返す（未対応） |

**LivePocketの新旧分離**: 旧システム (`t.livepocket.jp`) と新システム (`livepocket.jp`) はドメインが異なりHTMLの構造も別物なため、個別エクストラクタで対応している。

---

## paylove.org の REST API

paylove.org は SPA で、静的HTMLに会場情報を含まない。  
公開 REST API が存在し、イベントIDを渡すと会場名を直接返す。

```
GET https://paylove.org/api/events/{eventId}

レスポンス:
{
  "data": {
    "venue": "GOTANDA G6",
    ...
  }
}
```

URLパターン: `https://paylove.org/events/{eventId}` → eventId を取り出してAPIに渡す。

---

## 処理フロー

```
getVenue(ticketUrl)
  ├─ paylove.org → _getVenuePaylove() → REST API → venue または None
  ├─ 対応ドメイン → _EXTRACTORS[domain](html) → regex → venue または None
  └─ 未対応ドメイン → None
```

---

## 依存ライブラリ

- `httpx` — HTTP クライアント（同期）

---

## 調査メモ（実装時の知見）

- **tiget.net**: meta description タグに `会場：会場名` 形式で構造化されている。タグの属性順が `content-first`（`<meta content="..." name="description">`）のため、`name-first` と両パターンに対応している
- **ticketdive.com**: `>会場</span>` の直後 span に会場名
- **ticketvillage.jp**: `■ 会場` の後にスペース区切りで会場名
- **livepocket.jp**: `event-detail-info__place` クラスを含む `<dt>` → 対応 `<dd>` に会場名
- **paylove.org**: SPA のため HTML スクレイピング不可。`/api/events/` エンドポイントが公開されている
