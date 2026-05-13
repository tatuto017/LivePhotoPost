"""venue_scraper モジュールのユニットテスト。"""

from unittest.mock import MagicMock, patch

import pytest

from src.venue_scraper import getVenue


# --- HTMLフィクスチャ ---

TIGET_CONTENT_FIRST_HTML = """\
<html><head>
<meta content="開催日:2026年03月15日(日) 出演:激ロック 会場:clubasia 東京激ロックDJパーティー" name="description" />
</head><body></body></html>
"""

TIGET_NAME_FIRST_HTML = """\
<html><head>
<meta name="description" content="開催日:2026年03月15日(日) 会場：ZEPP TOKYO SPECIAL LIVE" />
</head><body></body></html>
"""

TIGET_NO_VENUE_HTML = """\
<html><head>
<meta content="開催日:2026年03月15日(日) 出演:激ロック" name="description" />
</head><body></body></html>
"""

TIGET_DETAIL_TABLE_HTML = """\
<html><body>
<dl class="pg-event__detail__section"><dt class="pg-event__detail__title">会場</dt><dd class="pg-event__detail__contents"><a target="_blank" href="https://maps.google.com/?cid=11911261503502514313">clubasia(東京都)<svg height="14.29" viewBox="0 0 10 14.29" width="10" xmlns="http://www.w3.org/2000/svg"><g><path d="M5,0A5,5,0,0,0,0,5c0,3.75,5,9.29,5,9.29S10,8.75,10,5A5,5,0,0,0,5,0ZM5,6A2,2,0,1,1,7,4,2,2,0,0,1,5,6Z" fill="#999"></path></g></svg></a></dd></dl>
</body></html>
"""

LIVEPOCKET_OLD_HTML = """\
<html><body>
[会場]Zepp Shinjuku (TOKYO)
<p>イベント詳細</p>
</body></html>
"""

LIVEPOCKET_NEW_HTML = """\
<html><body>
<span class="event-detail-info__place-label">会場</span>
<dd class="value">EX THEATER ROPPONGI</dd>
</body></html>
"""

TICKETDIVE_HTML = """\
<html><body>
<span>会場</span><span class="venue">渋谷CLUB QUATTRO</span>
</body></html>
"""

TICKETVILLAGE_HTML = """\
<html><body>
■ 会場　Zepp Osaka Bayside
イベント詳細
</body></html>
"""

PAYLOVE_JSON = {
    "data": {
        "venue": "CLUB CITTA'"
    }
}


# --- _fetchHtml / httpx パッチ用ヘルパー ---

def _mock_http_get(html: str, status_code: int = 200):
    """httpx.get をモックする際のレスポンスを生成する。"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# --- tiget.net ---

class TestExtractTiget:
    """tiget.net の会場名抽出テスト。"""

    def test_contentFirstMetaTag(self):
        """content-first 形式の meta description から会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(TIGET_CONTENT_FIRST_HTML)):
            result = getVenue("https://tiget.net/events/454587")
        assert result == "clubasia"

    def test_nameFirstMetaTag(self):
        """name-first 形式の meta description から会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(TIGET_NAME_FIRST_HTML)):
            result = getVenue("https://tiget.net/events/999")
        assert result == "ZEPP"

    def test_detailTable(self):
        """詳細テーブルの dt/dd/a パターンから会場名を抽出し、都道府県サフィックスを除去できる。"""
        with patch("httpx.get", return_value=_mock_http_get(TIGET_DETAIL_TABLE_HTML)):
            result = getVenue("https://tiget.net/events/454587")
        assert result == "clubasia"

    def test_noVenueInDescription(self):
        """meta description に会場情報がない場合は None を返す。"""
        with patch("httpx.get", return_value=_mock_http_get(TIGET_NO_VENUE_HTML)):
            result = getVenue("https://tiget.net/events/1")
        assert result is None

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("network error")):
            result = getVenue("https://tiget.net/events/1")
        assert result is None


# --- t.livepocket.jp ---

class TestExtractLivepocketOld:
    """t.livepocket.jp の会場名抽出テスト。"""

    def test_venueFound(self):
        """[会場]会場名 パターンから会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(LIVEPOCKET_OLD_HTML)):
            result = getVenue("https://t.livepocket.jp/e/test")
        assert result == "Zepp Shinjuku (TOKYO)"

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = getVenue("https://t.livepocket.jp/e/test")
        assert result is None


# --- livepocket.jp ---

class TestExtractLivepocketNew:
    """livepocket.jp の会場名抽出テスト。"""

    def test_venueFound(self):
        """event-detail-info__place の dd から会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(LIVEPOCKET_NEW_HTML)):
            result = getVenue("https://livepocket.jp/e/test")
        assert result == "EX THEATER ROPPONGI"

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = getVenue("https://livepocket.jp/e/test")
        assert result is None


# --- ticketdive.com ---

class TestExtractTicketdive:
    """ticketdive.com の会場名抽出テスト。"""

    def test_venueFound(self):
        """会場ラベル直後の span から会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(TICKETDIVE_HTML)):
            result = getVenue("https://ticketdive.com/events/1")
        assert result == "渋谷CLUB QUATTRO"

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = getVenue("https://ticketdive.com/events/1")
        assert result is None


# --- ticketvillage.jp ---

class TestExtractTicketvillage:
    """ticketvillage.jp の会場名抽出テスト。"""

    def test_venueFound(self):
        """■ 会場　会場名 パターンから会場名を抽出できる。"""
        with patch("httpx.get", return_value=_mock_http_get(TICKETVILLAGE_HTML)):
            result = getVenue("https://ticketvillage.jp/events/1")
        assert result == "Zepp Osaka Bayside"

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = getVenue("https://ticketvillage.jp/events/1")
        assert result is None


# --- paylove.org ---

class TestGetVenuePaylove:
    """paylove.org の会場名取得テスト（REST API）。"""

    def test_venueFound(self):
        """REST API の venue フィールドから会場名を取得できる。"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = PAYLOVE_JSON
        with patch("httpx.get", return_value=mock_resp):
            result = getVenue("https://paylove.org/events/1538")
        assert result == "CLUB CITTA'"

    def test_missingVenueField(self):
        """API レスポンスに venue がない場合は None を返す。"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {}}
        with patch("httpx.get", return_value=mock_resp):
            result = getVenue("https://paylove.org/events/1538")
        assert result is None

    def test_fetchError(self):
        """HTTP エラー時は None を返す。"""
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = getVenue("https://paylove.org/events/1538")
        assert result is None


# --- 未対応ドメイン ---

class TestUnsupportedDomain:
    """未対応ドメインのテスト。"""

    def test_unknownDomain(self):
        """未対応ドメインは None を返す。"""
        result = getVenue("https://example.com/ticket/1")
        assert result is None
