"""データディレクトリの写真スキャンとEXIF日時取得モジュール。"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image

_EXIF_TAG_DATETIME_ORIGINAL = 36867
_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
_IMAGE_SUFFIXES = {".jpg", ".jpeg"}


@dataclass
class Photo:
    """写真情報を保持するデータクラス。

    Attributes:
        path: 写真ファイルのパス
        takenAt: 撮影日時。EXIFのDateTimeOriginalを優先し、なければファイルの作成日時を使用する
    """

    path: Path
    takenAt: datetime | None


class PhotoLoader:
    """データディレクトリから写真を読み込むクラス。

    Args:
        photoDir: 写真が格納されたルートディレクトリ
    """

    def __init__(self, photoDir: Path) -> None:
        """PhotoLoaderを初期化する。"""
        self._photoDir = photoDir

    def loadPhotos(self, subDir: str | None = None) -> list[Photo]:
        """指定ディレクトリ以下のJPG写真を読み込む。

        Args:
            subDir: スキャン対象のサブディレクトリ名。省略時はルート以下の全JPGを対象とする

        Returns:
            撮影日時の昇順にソートされたPhotoのリスト
        """
        scanDir = self._photoDir / subDir if subDir else self._photoDir
        photos = []

        for filePath in sorted(scanDir.rglob("*")):
            if filePath.suffix.lower() not in _IMAGE_SUFFIXES:
                continue
            if "skip" in filePath.relative_to(scanDir).parts:
                continue
            photo = self._loadPhoto(filePath)
            if photo is not None:
                photos.append(photo)

        # 撮影日時の昇順。takenAtがNoneのものは末尾に配置
        photos.sort(key=lambda p: (p.takenAt is None, p.takenAt or datetime.min))
        return photos

    def _loadPhoto(self, filePath: Path) -> Photo | None:
        """1枚の写真ファイルを読み込む。

        画像のオープンに失敗した場合はNoneを返す。
        """
        try:
            img = Image.open(filePath)
            takenAt = self._readTakenAt(img)
            if takenAt is None:
                takenAt = datetime.fromtimestamp(filePath.stat().st_ctime)
            return Photo(path=filePath, takenAt=takenAt)
        except Exception:
            return None

    def _readTakenAt(self, img: Image.Image) -> datetime | None:
        """画像オブジェクトからDateTimeOriginalを取得する。

        Args:
            img: PILの画像オブジェクト

        Returns:
            撮影日時。EXIFがない、またはDateTimeOriginalが存在しない場合はNone
        """
        exif = img._getexif()
        if not exif:
            return None
        raw = exif.get(_EXIF_TAG_DATETIME_ORIGINAL)
        if not raw:
            return None
        try:
            return datetime.strptime(raw, _DATETIME_FORMAT)
        except ValueError:
            return None
