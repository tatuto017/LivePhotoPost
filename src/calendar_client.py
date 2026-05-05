"""iCalフィードの取得と撮影日時に近いイベント検索モジュール。"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from icalendar import Calendar

_URL_PATTERN = re.compile(r'https?://[^\s<>"\'&]+')


@dataclass
class Event:
    """カレンダーイベント情報を保持するデータクラス。

    Attributes:
        summary: イベントのタイトル
        startAt: イベント開始日時
        url: チケットサイト等のURL。存在しない場合はNone
    """

    summary: str
    startAt: datetime
    url: Optional[str]


class CalendarClient:
    """iCalフィードを取得してイベントを検索するクラス。

    Args:
        calendarUrl: Google CalendarのiCalフィードURL
        httpClient: HTTPクライアント。省略時はhttpx.Clientを生成する
    """

    def __init__(self, calendarUrl: str, httpClient: Optional[httpx.Client] = None) -> None:
        """CalendarClientを初期化する。"""
        self._calendarUrl = calendarUrl
        self._httpClient = httpClient or httpx.Client()

    def fetchEvents(self) -> list[Event]:
        """iCalフィードを取得してEventリストを返す。

        Returns:
            パースされたEventのリスト

        Raises:
            httpx.HTTPError: HTTP通信に失敗した場合
        """
        response = self._httpClient.get(self._calendarUrl)
        response.raise_for_status()

        cal = Calendar.from_ical(response.content)
        events = []
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            event = self._parseEvent(component)
            if event is not None:
                events.append(event)
        return events

    def findNearestEvent(self, takenAt: datetime, events: list[Event]) -> Optional[Event]:
        """撮影日時に最も近いイベントを返す。

        Args:
            takenAt: 写真の撮影日時（タイムゾーンなし）
            events: 検索対象のEventリスト

        Returns:
            最も近いEvent。リストが空の場合はNone
        """
        if not events:
            return None

        def timeDiff(event: Event):
            startAt = event.startAt
            # 終日イベントは datetime.date で来るので midnight の datetime に変換する
            if not isinstance(startAt, datetime):
                startAt = datetime(startAt.year, startAt.month, startAt.day)
            # タイムゾーン情報を除去してnaiveなdatetimeで比較する
            if startAt.tzinfo is not None:
                startAt = startAt.replace(tzinfo=None)
            return abs(startAt - takenAt)

        return min(events, key=timeDiff)

    def _parseEvent(self, component) -> Optional[Event]:
        """VEVENTコンポーネントをEventに変換する。

        Args:
            component: icalendarのVEVENTコンポーネント

        Returns:
            Eventオブジェクト。必須フィールドが欠けている場合はNone
        """
        summary = component.get("SUMMARY")
        dtstart = component.get("DTSTART")
        if summary is None or dtstart is None:
            return None

        url_prop = component.get("URL")
        if url_prop:
            url = str(url_prop)
        else:
            # URL プロパティがない場合は DESCRIPTION から抽出する
            desc = str(component.get("DESCRIPTION", ""))
            match = _URL_PATTERN.search(desc)
            url = match.group(0) if match else None

        return Event(
            summary=str(summary),
            startAt=dtstart.dt if hasattr(dtstart, "dt") else dtstart,
            url=url,
        )
