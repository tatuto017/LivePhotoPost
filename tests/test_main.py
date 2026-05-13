"""main モジュールのユニットテスト。"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.calendar_client import Event
from src.photo_loader import Photo
from src.main import run


def _makePhoto(
    path: Path | None = None,
    takenAt: datetime | None = datetime(2026, 3, 22, 18, 26, 27),
) -> Photo:
    return Photo(path=path or Path("/tmp/photo.jpg"), takenAt=takenAt)


def _makeEvent(
    summary: str = "テストライブ",
    startAt: datetime = datetime(2026, 3, 22, 18, 0, 0),
    url: str | None = "https://t.livepocket.jp/e/test",
) -> Event:
    return Event(summary=summary, startAt=startAt, url=url)


class TestRun:
    """run() のテスト。"""

    def _makePhotoLoader(self, photosBySubdir: dict[str, list[Photo]]) -> MagicMock:
        loader = MagicMock()
        loader.loadPhotos.side_effect = lambda subDir=None: photosBySubdir.get(subDir, [])
        return loader

    def _makeCalendarClient(self, events: list[Event], nearest: Event | None) -> MagicMock:
        client = MagicMock()
        client.fetchEvents.return_value = events
        client.findNearestEvent.return_value = nearest
        return client

    def _makeXPoster(self) -> MagicMock:
        poster = MagicMock()
        poster.post.return_value = "tweet_id_123"
        return poster

    def test_run_skips_actor_with_no_photos(self, tmp_path):
        """写真がない被写体ディレクトリはスキップする。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photoLoader = self._makePhotoLoader({"actor_a": []})
        event = _makeEvent()
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()

    def test_run_skips_photo_without_taken_at(self, tmp_path):
        """takenAt が None の写真はスキップする。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photo = _makePhoto(takenAt=None)
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        event = _makeEvent()
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()

    def test_run_skips_when_no_nearest_event(self, tmp_path):
        """最寄りイベントが見つからない場合はスキップする。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photo = _makePhoto()
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([], None)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()

    def test_run_skips_when_event_has_no_url(self, tmp_path):
        """イベントに URL がない場合はスキップする。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photo = _makePhoto()
        event = _makeEvent(url=None)
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()

    def test_run_skips_when_venue_not_found(self, tmp_path):
        """会場名が取得できない場合はスキップディレクトリに移動する。"""
        photoDir = tmp_path / "photo_dir"
        actorDir = photoDir / "actor_a"
        actorDir.mkdir(parents=True)
        photoFile = actorDir / "photo.jpg"
        photoFile.touch()
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photo = _makePhoto(path=photoFile)
        event = _makeEvent()
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value=None):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()
        assert not photoFile.exists()
        assert (actorDir / "skip" / "photo.jpg").exists()

    def test_run_skips_actor_without_template(self, tmp_path):
        """テンプレートファイルがない被写体はスキップする。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()

        photo = _makePhoto()
        event = _makeEvent()
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 0
        xPoster.post.assert_not_called()

    def test_run_skips_non_directory_entries(self, tmp_path):
        """photoDir 直下のファイル（非ディレクトリ）は無視する。"""
        photoDir = tmp_path / "photo_dir"
        photoDir.mkdir()
        (photoDir / "some_file.txt").write_text("not a dir")
        (photoDir / "actor_a").mkdir()
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        (templateDir / "actor_a.txt").write_text("{date}\n{event_name}\n{venue}")

        photo = _makePhoto()
        event = _makeEvent()
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 1

    def test_run_posts_photo_successfully(self, tmp_path):
        """全条件を満たす場合に写真を投稿する。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        templateText = "{date}\n{event_name}\n{venue}"
        (templateDir / "actor_a.txt").write_text(templateText)

        photo = _makePhoto()
        event = _makeEvent()
        photoLoader = self._makePhotoLoader({"actor_a": [photo]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 1
        xPoster.post.assert_called_once_with(photo, event, "渋谷O-WEST", templateText)

    def test_run_posts_multiple_actors(self, tmp_path):
        """複数の被写体ディレクトリに対してそれぞれ投稿する。"""
        photoDir = tmp_path / "photo_dir"
        for actor in ["actor_a", "actor_b"]:
            (photoDir / actor).mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        templateText = "{date}\n{event_name}\n{venue}"
        (templateDir / "actor_a.txt").write_text(templateText)
        (templateDir / "actor_b.txt").write_text(templateText)

        photo_a = _makePhoto(path=Path("/tmp/a.jpg"))
        photo_b = _makePhoto(path=Path("/tmp/b.jpg"))
        photoLoader = self._makePhotoLoader({"actor_a": [photo_a], "actor_b": [photo_b]})
        event = _makeEvent()
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 2
        assert xPoster.post.call_count == 2

    def test_run_posts_first_photo_only(self, tmp_path):
        """被写体ディレクトリ内に複数写真がある場合、最初の1枚だけ投稿する。"""
        photoDir = tmp_path / "photo_dir"
        (photoDir / "actor_a").mkdir(parents=True)
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        templateText = "{date}\n{event_name}\n{venue}"
        (templateDir / "actor_a.txt").write_text(templateText)

        photo1 = _makePhoto(path=Path("/tmp/photo1.jpg"), takenAt=datetime(2026, 3, 22, 18, 0))
        photo2 = _makePhoto(path=Path("/tmp/photo2.jpg"), takenAt=datetime(2026, 3, 22, 19, 0))
        photoLoader = self._makePhotoLoader({"actor_a": [photo1, photo2]})
        event = _makeEvent()
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", return_value="渋谷O-WEST"):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 1
        xPoster.post.assert_called_once_with(photo1, event, "渋谷O-WEST", templateText)

    def test_run_moves_venue_failure_to_skip_and_posts_next(self, tmp_path):
        """会場名取得失敗の写真をスキップディレクトリに移動し、次の写真を投稿する。"""
        photoDir = tmp_path / "photo_dir"
        actorDir = photoDir / "actor_a"
        actorDir.mkdir(parents=True)
        photo1File = actorDir / "photo1.jpg"
        photo1File.touch()
        templateDir = tmp_path / "template"
        templateDir.mkdir()
        templateText = "{date}\n{event_name}\n{venue}"
        (templateDir / "actor_a.txt").write_text(templateText)

        photo1 = _makePhoto(path=photo1File, takenAt=datetime(2026, 3, 22, 18, 0))
        photo2 = _makePhoto(path=Path("/tmp/photo2.jpg"), takenAt=datetime(2026, 3, 22, 19, 0))
        event = _makeEvent()
        photoLoader = self._makePhotoLoader({"actor_a": [photo1, photo2]})
        calendarClient = self._makeCalendarClient([event], event)
        xPoster = self._makeXPoster()

        with patch("src.main.getVenue", side_effect=[None, "渋谷O-WEST"]):
            result = run(photoLoader, calendarClient, xPoster, templateDir, photoDir)

        assert result == 1
        xPoster.post.assert_called_once_with(photo2, event, "渋谷O-WEST", templateText)
        assert not photo1File.exists()
        assert (actorDir / "skip" / "photo1.jpg").exists()
