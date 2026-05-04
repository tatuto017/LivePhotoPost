"""エントリーポイント・モジュール統合。"""

import os
from pathlib import Path

from src.calendar_client import CalendarClient
from src.photo_loader import PhotoLoader
from src.venue_scraper import getVenue
from src.x_poster import XPoster, createXPosterFromEnv


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

        templatePath = templateDir / f"{actorId}.txt"
        if not templatePath.exists():
            continue
        templateText = templatePath.read_text(encoding="utf-8")

        photos = photoLoader.loadPhotos(subDir=actorId)
        if not photos:
            continue

        photo = photos[0]
        if photo.takenAt is None:
            continue

        event = calendarClient.findNearestEvent(photo.takenAt, events)
        if event is None:
            continue

        if not event.url:
            continue

        venue = getVenue(event.url)
        if not venue:
            continue

        xPoster.post(photo, event, venue, templateText)
        postedCount += 1

    return postedCount


def main() -> None:
    """環境変数から設定を読み込んで run を実行する。"""
    photoDir = Path(os.environ["PHOTO_DIR"])
    calendarUrl = os.environ["CALENDAR"]

    photoLoader = PhotoLoader(photoDir)
    calendarClient = CalendarClient(calendarUrl)
    xPoster = createXPosterFromEnv()
    templateDir = Path(__file__).parent.parent / "template"

    count = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)
    print(f"Posted {count} photos")


if __name__ == "__main__":
    main()
