"""エントリーポイント・モジュール統合。"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.calendar_client import CalendarClient
from src.photo_loader import PhotoLoader
from src.venue_scraper import getVenue
from src.x_poster import XPoster, createXPosterFromEnv


def _log(actorId: str, msg: str) -> None:
    """タイムスタンプ付きでログを出力する。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{actorId}] {msg}")


def run(
    photoLoader: PhotoLoader,
    calendarClient: CalendarClient,
    xPoster: XPoster,
    templateDir: Path,
    photoDir: Path,
) -> int:
    """メイン処理を実行する。

    Args:
        photoLoader: 写真読み込みクライアント
        calendarClient: カレンダークライアント
        xPoster: X 投稿クライアント
        templateDir: テンプレートファイルのディレクトリ
        photoDir: 被写体別写真ディレクトリのルートパス

    Returns:
        投稿した写真の枚数
    """
    events = calendarClient.fetchEvents()
    postedCount = 0

    for actorDir in sorted(photoDir.iterdir()):
        if not actorDir.is_dir():
            continue

        actorId = actorDir.name
        _log(actorId, "処理開始")

        templatePath = templateDir / f"{actorId}.txt"
        if not templatePath.exists():
            _log(actorId, f"SKIP: テンプレートなし ({templatePath})")
            continue
        templateText = templatePath.read_text(encoding="utf-8")

        photos = photoLoader.loadPhotos(subDir=actorId)
        if not photos:
            _log(actorId, "SKIP: 写真なし")
            continue

        for photo in photos:
            if photo.takenAt is None:
                _log(actorId, f"SKIP: EXIF日時取得不可 ({photo.path})")
                continue

            _log(actorId, f"撮影日時: {photo.takenAt}")

            event = calendarClient.findNearestEvent(photo.takenAt, events)
            if event is None:
                _log(actorId, "SKIP: カレンダーイベントなし")
                continue

            _log(actorId, f"イベント: {event.summary} ({event.startAt}) url={event.url}")

            if not event.url:
                _log(actorId, "SKIP: イベントにURL未設定")
                continue

            venue = getVenue(event.url)
            if not venue:
                _log(actorId, f"SKIP: 会場名取得失敗 (url={event.url})")
                skipDir = actorDir / "skip"
                skipDir.mkdir(exist_ok=True)
                photo.path.rename(skipDir / photo.path.name)
                continue

            _log(actorId, f"会場: {venue}")
            xPoster.post(photo, event, venue, templateText)
            postedCount += 1
            break

    return postedCount


def main() -> None:
    """環境変数から設定を読み込んで run を実行する。"""
    load_dotenv()
    photoDir = Path(os.environ["PHOTO_DIR"])
    calendarUrl = os.environ["CALENDAR"]

    photoLoader = PhotoLoader(photoDir)
    calendarClient = CalendarClient(calendarUrl)
    xPoster = createXPosterFromEnv()
    templateDir = Path(__file__).parent.parent / "template"

    count = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Posted {count} photos")


if __name__ == "__main__":
    main()
