"""calendar_client モジュールのユニットテスト。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.calendar_client import CalendarClient, Event


_SAMPLE_ICS = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//Google Inc//Google Calendar 70.9054//EN\r\n"
    "BEGIN:VEVENT\r\n"
    "SUMMARY:テストライブ\r\n"
    "DTSTART:20260322T090000Z\r\n"
    "DTEND:20260322T120000Z\r\n"
    "URL:https://t.livepocket.jp/e/test-live\r\n"
    "END:VEVENT\r\n"
    "BEGIN:VEVENT\r\n"
    "SUMMARY:別のライブ\r\n"
    "DTSTART:20260401T060000Z\r\n"
    "DTEND:20260401T090000Z\r\n"
    "URL:https://tiget.net/events/456\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
).encode("utf-8")

_ICS_NO_URL = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "BEGIN:VEVENT\r\n"
    "SUMMARY:URLなしライブ\r\n"
    "DTSTART:20260322T090000Z\r\n"
    "DTEND:20260322T120000Z\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
).encode("utf-8")


class TestEvent:
    """Event データクラスのテスト。"""

    def test_event_has_summary_startAt_url(self):
        event = Event(
            summary="テストライブ",
            startAt=datetime(2026, 3, 22, 18, 0, 0),
            url="https://t.livepocket.jp/e/test",
        )
        assert event.summary == "テストライブ"
        assert event.startAt == datetime(2026, 3, 22, 18, 0, 0)
        assert event.url == "https://t.livepocket.jp/e/test"

    def test_event_url_can_be_none(self):
        event = Event(summary="ライブ", startAt=datetime(2026, 3, 22, 18, 0, 0), url=None)
        assert event.url is None


class TestCalendarClientFetchEvents:
    """CalendarClient.fetchEvents のテスト。"""

    def _makeClient(self, ics_content: bytes) -> CalendarClient:
        """モック httpx.Client を注入した CalendarClient を生成する。"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = ics_content

        mock_http = MagicMock()
        mock_http.get.return_value = mock_response

        return CalendarClient(
            calendarUrl="https://example.com/cal.ics",
            httpClient=mock_http,
        )

    def test_fetchEvents_returns_event_list(self):
        """ICSを取得してEventリストを返す。"""
        client = self._makeClient(_SAMPLE_ICS)
        events = client.fetchEvents()
        assert len(events) == 2

    def test_fetchEvents_parses_summary(self):
        """SUMMARY フィールドを summary に格納する。"""
        client = self._makeClient(_SAMPLE_ICS)
        events = client.fetchEvents()
        summaries = {e.summary for e in events}
        assert "テストライブ" in summaries
        assert "別のライブ" in summaries

    def test_fetchEvents_parses_url(self):
        """URL フィールドを url に格納する。"""
        client = self._makeClient(_SAMPLE_ICS)
        events = client.fetchEvents()
        urls = {e.url for e in events}
        assert "https://t.livepocket.jp/e/test-live" in urls

    def test_fetchEvents_event_without_url_sets_none(self):
        """URL がない VEVENT は url=None になる。"""
        client = self._makeClient(_ICS_NO_URL)
        events = client.fetchEvents()
        assert len(events) == 1
        assert events[0].url is None

    def test_fetchEvents_parses_startAt(self):
        """DTSTART を startAt に格納する。"""
        client = self._makeClient(_SAMPLE_ICS)
        events = client.fetchEvents()
        # UTC 9時 = JST 18時
        start_utc = datetime(2026, 3, 22, 9, 0, 0, tzinfo=timezone.utc)
        starts = {e.startAt for e in events}
        assert start_utc in starts

    def test_fetchEvents_calls_get_with_calendar_url(self):
        """httpClient.get を calendarUrl で呼び出す。"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = _SAMPLE_ICS

        mock_http = MagicMock()
        mock_http.get.return_value = mock_response

        client = CalendarClient(
            calendarUrl="https://example.com/cal.ics",
            httpClient=mock_http,
        )
        client.fetchEvents()

        mock_http.get.assert_called_once_with("https://example.com/cal.ics")

    def test_fetchEvents_raises_on_http_error(self):
        """HTTP エラー時は例外を送出する。"""
        import httpx

        mock_http = MagicMock()
        mock_http.get.side_effect = httpx.HTTPError("connection failed")

        client = CalendarClient(
            calendarUrl="https://example.com/cal.ics",
            httpClient=mock_http,
        )
        with pytest.raises(httpx.HTTPError):
            client.fetchEvents()


class TestCalendarClientFindNearestEvent:
    """CalendarClient.findNearestEvent のテスト。"""

    def _makeClient(self) -> CalendarClient:
        return CalendarClient(calendarUrl="https://example.com/cal.ics")

    def test_findNearestEvent_returns_none_for_empty_list(self):
        """イベントリストが空の場合 None を返す。"""
        client = self._makeClient()
        result = client.findNearestEvent(
            takenAt=datetime(2026, 3, 22, 18, 0, 0),
            events=[],
        )
        assert result is None

    def test_findNearestEvent_returns_single_event(self):
        """イベントが1件のみの場合そのイベントを返す。"""
        events = [Event(summary="ライブ", startAt=datetime(2026, 3, 22, 18, 0, 0), url=None)]
        client = self._makeClient()
        result = client.findNearestEvent(
            takenAt=datetime(2026, 3, 22, 19, 0, 0),
            events=events,
        )
        assert result.summary == "ライブ"

    def test_findNearestEvent_returns_closest_event(self):
        """複数イベントの中から撮影日時に最も近いイベントを返す。"""
        events = [
            Event(summary="近いライブ", startAt=datetime(2026, 3, 22, 18, 0, 0), url=None),
            Event(summary="遠いライブ", startAt=datetime(2026, 4, 1, 15, 0, 0), url=None),
        ]
        client = self._makeClient()
        result = client.findNearestEvent(
            takenAt=datetime(2026, 3, 22, 19, 0, 0),
            events=events,
        )
        assert result.summary == "近いライブ"

    def test_findNearestEvent_takenAt_before_event(self):
        """撮影日時がイベント開始前でも正しく最近傍を返す。"""
        events = [
            Event(summary="当日ライブ", startAt=datetime(2026, 3, 22, 18, 0, 0), url=None),
            Event(summary="翌日ライブ", startAt=datetime(2026, 3, 23, 18, 0, 0), url=None),
        ]
        client = self._makeClient()
        result = client.findNearestEvent(
            takenAt=datetime(2026, 3, 22, 17, 0, 0),
            events=events,
        )
        assert result.summary == "当日ライブ"

    def test_findNearestEvent_handles_timezone_aware_startAt(self):
        """startAt がタイムゾーン付きでも比較できる。"""
        events = [
            Event(
                summary="UTC イベント",
                startAt=datetime(2026, 3, 22, 9, 0, 0, tzinfo=timezone.utc),
                url=None,
            ),
        ]
        client = self._makeClient()
        # JST 18:00 = UTC 9:00 に撮影
        result = client.findNearestEvent(
            takenAt=datetime(2026, 3, 22, 18, 0, 0),
            events=events,
        )
        assert result.summary == "UTC イベント"
