"""X (Twitter) への写真投稿モジュール。"""

import os

import tweepy

from src.calendar_client import Event
from src.photo_loader import Photo


class XPoster:
    """X に写真を投稿するクラス。

    メディアアップロードに v1.1 API、ツイート投稿に v2 API を使用する。

    Args:
        apiClient: Tweepy v1.1 API クライアント（メディアアップロード用）
        v2Client: Tweepy v2 Client（ツイート投稿用）
    """

    def __init__(self, apiClient: tweepy.API, v2Client: tweepy.Client) -> None:
        """XPoster を初期化する。"""
        self._api = apiClient
        self._client = v2Client

    def buildText(self, templateText: str, event: Event, venue: str) -> str:
        """テンプレートのプレースホルダーを置換して投稿テキストを生成する。

        Args:
            templateText: {date}、{event_name}、{venue} を含むテンプレート文字列
            event: カレンダーイベント
            venue: 会場名

        Returns:
            プレースホルダーを置換した投稿テキスト
        """
        return (
            templateText
            .replace("{date}", event.startAt.strftime("%Y/%m/%d"))
            .replace("{event_name}", event.summary)
            .replace("{venue}", venue)
        )

    def post(self, photo: Photo, event: Event, venue: str, templateText: str) -> str:
        """写真を X に投稿し、投稿後に写真ファイルを削除する。

        Args:
            photo: 投稿する写真
            event: 関連カレンダーイベント
            venue: 会場名
            templateText: 投稿テキストのテンプレート

        Returns:
            投稿されたツイートの ID 文字列

        Raises:
            Exception: メディアアップロードまたはツイート送信に失敗した場合（写真は削除されない）
        """
        text = self.buildText(templateText, event, venue)
        media = self._api.media_upload(filename=str(photo.path))
        response = self._client.create_tweet(text=text, media_ids=[media.media_id])
        photo.path.unlink()
        return str(response.data["id"])


def createXPosterFromEnv() -> XPoster:
    """環境変数（Infisical 経由）から認証情報を読み込んで XPoster を生成する。

    環境変数:
        API_KEY: X API キー
        API_SECRET: X API シークレット
        ACCESS_TOKEN: アクセストークン
        ACCESS_TOKEN_SECRET: アクセストークンシークレット

    Returns:
        XPoster インスタンス
    """
    auth = tweepy.OAuth1UserHandler(
        consumer_key=os.environ["API_KEY"],
        consumer_secret=os.environ["API_SECRET"],
        access_token=os.environ["ACCESS_TOKEN"],
        access_token_secret=os.environ["ACCESS_TOKEN_SECRET"],
    )
    client = tweepy.Client(
        consumer_key=os.environ["API_KEY"],
        consumer_secret=os.environ["API_SECRET"],
        access_token=os.environ["ACCESS_TOKEN"],
        access_token_secret=os.environ["ACCESS_TOKEN_SECRET"],
    )
    return XPoster(apiClient=tweepy.API(auth), v2Client=client)
