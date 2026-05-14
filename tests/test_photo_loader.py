"""photo_loader モジュールのユニットテスト。"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.photo_loader import Photo, PhotoLoader


class TestPhoto:
    """Photo データクラスのテスト。"""

    def test_photo_has_path_and_takenAt(self):
        photo = Photo(path=Path("/tmp/img.jpg"), takenAt=datetime(2026, 3, 22, 18, 26, 27))
        assert photo.path == Path("/tmp/img.jpg")
        assert photo.takenAt == datetime(2026, 3, 22, 18, 26, 27)

    def test_photo_takenAt_can_be_none(self):
        photo = Photo(path=Path("/tmp/img.jpg"), takenAt=None)
        assert photo.takenAt is None


class TestPhotoLoader:
    """PhotoLoader クラスのテスト。"""

    def test_loadPhotos_returns_photos_with_exif(self, tmp_path):
        """JPGファイルを読み込み、EXIFのDateTimeOriginalをtakenAtに設定する。"""
        img_path = tmp_path / "photo.jpg"
        img_path.touch()

        mock_exif = {36867: "2026:03:22 18:26:27"}  # 36867 = DateTimeOriginal tag ID
        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = mock_exif
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 1
        assert photos[0].path == img_path
        assert photos[0].takenAt == datetime(2026, 3, 22, 18, 26, 27)

    def test_loadPhotos_with_subDir(self, tmp_path):
        """subDirを指定すると、そのサブディレクトリ内のJPGのみ返す。"""
        sub = tmp_path / "kmrnc_kai"
        sub.mkdir()
        (sub / "photo1.jpg").touch()
        (sub / "photo2.JPEG").touch()
        other = tmp_path / "other"
        other.mkdir()
        (other / "photo3.jpg").touch()

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos(subDir="kmrnc_kai")

        assert len(photos) == 2
        assert all(p.path.parent == sub for p in photos)

    def test_loadPhotos_without_subDir_scans_all(self, tmp_path):
        """subDir未指定時は全サブディレクトリのJPGを返す。"""
        for name in ("dir_a", "dir_b"):
            d = tmp_path / name
            d.mkdir()
            (d / "img.jpg").touch()

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 2

    def test_loadPhotos_skips_non_image_files(self, tmp_path):
        """JPG/JPEG以外のファイルはスキップする。"""
        (tmp_path / "photo.jpg").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "photo.png").touch()

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 1
        assert photos[0].path.suffix.lower() == ".jpg"

    def test_loadPhotos_no_exif_uses_file_ctime(self, tmp_path):
        """EXIFがない場合、takenAtはファイルの作成日時（ctime）になる。"""
        img_path = tmp_path / "photo.jpg"
        img_path.touch()
        expected = datetime.fromtimestamp(img_path.stat().st_ctime)

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 1
        assert photos[0].takenAt == expected

    def test_loadPhotos_no_datetimeoriginal_in_exif_uses_file_ctime(self, tmp_path):
        """EXIFにDateTimeOriginalがない場合、takenAtはファイルの作成日時になる。"""
        img_path = tmp_path / "photo.jpg"
        img_path.touch()
        expected = datetime.fromtimestamp(img_path.stat().st_ctime)

        # DateTimeOriginal (36867) を含まないEXIF
        mock_exif = {271: "Canon", 272: "EOS R5"}
        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = mock_exif
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert photos[0].takenAt == expected

    def test_loadPhotos_empty_directory(self, tmp_path):
        """空のディレクトリでは空リストを返す。"""
        loader = PhotoLoader(photoDir=tmp_path)
        photos = loader.loadPhotos()
        assert photos == []

    def test_loadPhotos_sorted_by_takenAt(self, tmp_path):
        """複数写真はtakenAt昇順にソートされる。"""
        (tmp_path / "a.jpg").touch()
        (tmp_path / "b.jpg").touch()

        exif_a = {36867: "2026:03:22 20:00:00"}
        exif_b = {36867: "2026:03:22 18:00:00"}

        def open_side_effect(path, *args, **kwargs):
            mock_img = MagicMock()
            if path.name == "a.jpg":
                mock_img._getexif.return_value = exif_a
            else:
                mock_img._getexif.return_value = exif_b
            return mock_img

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_image_cls.open.side_effect = open_side_effect

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert photos[0].takenAt == datetime(2026, 3, 22, 18, 0, 0)
        assert photos[1].takenAt == datetime(2026, 3, 22, 20, 0, 0)

    def test_loadPhotos_image_open_error_skips_file(self, tmp_path):
        """Imageのオープンに失敗したファイルはスキップする。"""
        (tmp_path / "broken.jpg").touch()
        (tmp_path / "good.jpg").touch()

        call_count = 0

        def open_side_effect(path, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if path.name == "broken.jpg":
                raise OSError("not a valid image")
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            return mock_img

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_image_cls.open.side_effect = open_side_effect

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 1
        assert photos[0].path.name == "good.jpg"

    def test_loadPhotos_excludes_skip_directory(self, tmp_path):
        """skip ディレクトリ内の写真は除外する。"""
        skip_dir = tmp_path / "skip"
        skip_dir.mkdir()
        (skip_dir / "skipped.jpg").touch()
        (tmp_path / "valid.jpg").touch()

        with patch("src.photo_loader.Image") as mock_image_cls:
            mock_img = MagicMock()
            mock_img._getexif.return_value = None
            mock_image_cls.open.return_value = mock_img

            loader = PhotoLoader(photoDir=tmp_path)
            photos = loader.loadPhotos()

        assert len(photos) == 1
        assert photos[0].path.name == "valid.jpg"
