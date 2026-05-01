"""チケットサイトから会場名を取得するモジュール。"""

import re
from urllib.parse import urlparse

import httpx

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
_TIMEOUT = 10


def getVenue(ticketUrl: str) -> str | None:
    """チケットURLから会場名を取得する。

    Args:
        ticketUrl: チケットサイトのURL

    Returns:
        会場名。取得できない場合はNone。
    """
    domain = urlparse(ticketUrl).netloc

    if domain == "paylove.org":
        return _getVenuePaylove(ticketUrl)

    extractor = _EXTRACTORS.get(domain)
    if extractor is None:
        return None

    html = _fetchHtml(ticketUrl)
    if not html:
        return None

    return extractor(html)


def _fetchHtml(url: str) -> str | None:
    """HTMLを取得する。"""
    try:
        resp = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _getVenuePaylove(url: str) -> str | None:
    """paylove.org: REST API の venue フィールドから直接取得する。

    URL例: https://paylove.org/events/1538
    API例: https://paylove.org/api/events/1538
    """
    try:
        eventId = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        apiUrl = f"https://paylove.org/api/events/{eventId}"
        resp = httpx.get(apiUrl, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("venue") or None
    except Exception:
        return None


# --- ドメイン別テキスト抽出 ---

def _extractLivepocketOld(html: str) -> str | None:
    """t.livepocket.jp: [会場]会場名 パターンで抽出。"""
    m = re.search(r"\[会場\]([^\[<\n\r&]{1,60})", html)
    return m.group(1).strip() if m else None


def _extractLivepocketNew(html: str) -> str | None:
    """livepocket.jp: event-detail-info__place の dd テキストで抽出。"""
    m = re.search(
        r'event-detail-info__place[^"]*">会場</span>'
        r".*?<dd[^>]*>\s*([^<\n]{1,60})",
        html,
        re.DOTALL,
    )
    return m.group(1).strip() if m else None


def _extractTiget(html: str) -> str | None:
    """tiget.net: meta description 内の 会場：会場名 パターンで抽出。"""
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html)
    if m:
        v = re.search(r"会場[：:]\s*([^\s　,、。\n<]{1,60})", m.group(1))
        if v:
            return v.group(1).strip()
    return None


def _extractTicketdive(html: str) -> str | None:
    """ticketdive.com: 会場ラベルの直後spanで抽出。"""
    m = re.search(r">会場</span><span[^>]*>([^<]{1,60})</span>", html)
    return m.group(1).strip() if m else None


def _extractTicketvillage(html: str) -> str | None:
    """ticketvillage.jp: ■ 会場　会場名 パターンで抽出。"""
    m = re.search(r"■\s*会場[\s　]+([^\n<\r]{1,60})", html)
    return m.group(1).strip() if m else None


_EXTRACTORS: dict[str, callable] = {
    "t.livepocket.jp":  _extractLivepocketOld,
    "livepocket.jp":    _extractLivepocketNew,
    "tiget.net":        _extractTiget,
    "ticketdive.com":   _extractTicketdive,
    "ticketvillage.jp": _extractTicketvillage,
    # paylove.org は getVenue() で REST API に直接ルーティング済み
}
