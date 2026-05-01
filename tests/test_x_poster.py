"""x_poster モジュールのユニットテスト。"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.calendar_client import Event
from src.photo_loader import Photo
from src.x_poster import XPoster


def _makeEvent(
    summary: str = "テストライブ",
    startAt: datetime = datetime(2026, 3, 22, 18, 0, 0),
    url: str | None = "https://t.livepocket.jp/e/test",
) -> Event:
    return Event(summary=summary, startAt=startAt, url=url)


def _makeXPoster() -> tuple[XPoster, MagicMock, MagicMock]:
    """モックを注入した XPoster を返す。(poster, api_client, v2_client)"""
    mock_api = MagicMock()
    mock_media = MagicMock()
    mock_media.media_id = 111222333
    mock_api.media_upload.return_value = mock_media

    mock_v2 = MagicMock()
    mock_response = MagicMock()
    mock_response.data = {"id": "9876543210"}
    mock_v2.create_tweet.return_value = mock_response

    poster = XPoster(apiClient=mock_api, v2Client=mock_v2)
    return poster, mock_api, mock_v2


class TestXPosterBuildText:
    """XPoster.buildText のテスト。"""

    def _poster(self) -> XPoster:
        poster, *_ = _makeXPoster()
        return poster

    def test_buildText_replaces_date(self):
        """{date} をイベント開始日の YYYY/MM/DD に置換する。"""
        event = _makeEvent(startAt=datetime(2026, 3, 22, 18, 0, 0))
        result = self._poster().buildText("{date}", event, "渋谷CLUB QUATTRO")
        assert result == "2026/03/22"

    def test_buildText_replaces_event_name(self):
        """{event_name} をイベントのサマリーに置換する。"""
        event = _makeEvent(summary="クモリノチ。春ワンマン")
        result = self._poster().buildText("{event_name}", event, "渋谷CLUB QUATTRO")
        assert result == "クモリノチ。春ワンマン"

    def test_buildText_replaces_venue(self):
        """{venue} を会場名に置換する。"""
        event = _makeEvent()
        result = self._poster().buildText("{venue}", event, "渋谷CLUB QUATTRO")
        assert result == "渋谷CLUB QUATTRO"

    def test_buildText_replaces_all_placeholders(self):
        """すべてのプレースホルダーを同時に置換する。"""
        event = _makeEvent(summary="春ライブ", startAt=datetime(2026, 3, 22, 18, 0, 0))
        template = "{date}\n{event_name}\n{venue}"
        result = self._poster().buildText(template, event, "Zepp Tokyo")
        assert result == "2026/03/22\n春ライブ\nZepp Tokyo"

    def test_buildText_no_placeholder_unchanged(self):
        """プレースホルダーがないテンプレートはそのまま返す。"""
        event = _makeEvent()
        result = self._poster().buildText("fixed text", event, "会場")
        assert result == "fixed text"


class TestXPosterPost:
    """XPoster.post のテスト。"""

    def test_post_calls_media_upload_with_photo_path(self, tmp_path: Path):
        """media_upload を写真のパス（str）で呼び出す。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent()

        poster, mock_api, _ = _makeXPoster()
        poster.post(photo, event, "会場名", "{date}")

        mock_api.media_upload.assert_called_once_with(filename=str(photo_file))

    def test_post_calls_create_tweet_with_text_and_media_id(self, tmp_path: Path):
        """create_tweet をテキストとメディアIDで呼び出す。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent(startAt=datetime(2026, 3, 22, 18, 0, 0))

        poster, _, mock_v2 = _makeXPoster()
        poster.post(photo, event, "渋谷CLUB QUATTRO", "{date}\n{venue}")

        mock_v2.create_tweet.assert_called_once_with(
            text="2026/03/22\n渋谷CLUB QUATTRO",
            media_ids=[111222333],
        )

    def test_post_returns_tweet_id(self, tmp_path: Path):
        """投稿成功時にツイートIDの文字列を返す。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent()

        poster, *_ = _makeXPoster()
        tweet_id = poster.post(photo, event, "会場名", "{date}")

        assert tweet_id == "9876543210"

    def test_post_deletes_photo_after_posting(self, tmp_path: Path):
        """投稿後に写真ファイルを削除する。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent()

        poster, *_ = _makeXPoster()
        poster.post(photo, event, "会場名", "{date}")

        assert not photo_file.exists()

    def test_post_does_not_delete_photo_on_upload_failure(self, tmp_path: Path):
        """メディアアップロード失敗時は写真を削除しない。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent()

        mock_api = MagicMock()
        mock_api.media_upload.side_effect = Exception("upload failed")
        poster = XPoster(apiClient=mock_api, v2Client=MagicMock())

        with pytest.raises(Exception, match="upload failed"):
            poster.post(photo, event, "会場名", "{date}")

        assert photo_file.exists()

    def test_post_does_not_delete_photo_on_tweet_failure(self, tmp_path: Path):
        """ツイート送信失敗時は写真を削除しない。"""
        photo_file = tmp_path / "photo.jpg"
        photo_file.write_bytes(b"dummy")
        photo = Photo(path=photo_file, takenAt=datetime(2026, 3, 22, 18, 0, 0))
        event = _makeEvent()

        mock_api = MagicMock()
        mock_media = MagicMock()
        mock_media.media_id = 111222333
        mock_api.media_upload.return_value = mock_media
        mock_v2 = MagicMock()
        mock_v2.create_tweet.side_effect = Exception("tweet failed")
        poster = XPoster(apiClient=mock_api, v2Client=mock_v2)

        with pytest.raises(Exception, match="tweet failed"):
            poster.post(photo, event, "会場名", "{date}")

        assert photo_file.exists()
