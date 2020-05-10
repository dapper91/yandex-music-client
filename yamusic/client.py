"""
Yandex music service client.
"""

import functools as ft
import json
import logging
import uuid
from collections import namedtuple
from typing import Any, Callable, List, Optional, Union

import requests

from yamusic import exceptions
from yamusic.models import Artist, Album, Genre, Playlist, Result, Track, Visibility, SearchType
from yamusic.models import SearchResult, SearchResultWrapper, Similar, TrackWrapper

logger = logging.getLogger(__package__)

# user oauth credentials
OAuthCred = namedtuple('OAuthCred', ('access_token', 'user_id'))


class YaMusicClient:
    """
    A Yandex music service client. Creates a client instance and authenticates
    on the service if login and password are provided.

    :param login: yandex account user name
    :param password: yandex account password
    :param device_id: local device id (will be automatically generated if omitted)
    :param app_uuid: unique identifier (will be automatically generated if omitted)
    :param auth_cred: authentication data, (access_token, user_id) pair
    """

    OAUTH_CLIENT_ID = '23cabbbdc6cd418abb4b39c32c41195d'
    OAUTH_CLIENT_SECRET = '53bc75238f0c4d08a118e51fe9203300'

    OAUTH_HOST = 'oauth.mobile.yandex.net'
    API_HOST = 'api.music.yandex.net'

    PACKAGE_NAME = 'ru.yandex.music'

    def __init__(
        self,
        login: Optional[str] = None,
        password: Optional[str] = None,
        *,
        device_id: Optional[str] = None,
        app_uuid: Optional[str] = None,
        oauth_cred: Optional[OAuthCred] = None
    ):
        self._login = login
        self._device_id = device_id or uuid.uuid4().hex
        self._app_uuid = app_uuid or uuid.uuid4().hex
        self._oauth_cred = oauth_cred or OAuthCred(None, None)

        if password is not None and login is not None:
            self.auth(login, password)

    def _request(
        self,
        method: str,
        host: str,
        path: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
        **kwargs: Any
    ) -> dict:
        if all(self._oauth_cred):
            headers = {**{'Authorization': 'OAuth ' + self._oauth_cred.access_token}, **(headers or {})}

        resp = requests.request(
            method=method,
            url=f'https://{host}/{path}',
            params=params,
            headers=headers,
            data=data,
            **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    def auth(self, login: str, password: str) -> None:
        """
        Authenticates on the service as a `login` user.

        :param login: yandex account user name
        :param password: yandex account password
        :raises `exceptions.AuthenticationError`: if the credentials are not valid
        """

        params = {
            'device_id': self._device_id,
            'uuid': self._app_uuid,
            'package_name': self.PACKAGE_NAME,
        }

        data = {
            'grant_type': 'password',
            'username': login,
            'password': password,
            'client_id': self.OAUTH_CLIENT_ID,
            'client_secret': self.OAUTH_CLIENT_SECRET
        }

        try:
            resp = self._request('POST', self.OAUTH_HOST, '1/token', params=params, data=data)
            access_token, user_id = resp.get('access_token'), int(resp.get('uid'))

            if access_token is None or user_id is None:
                raise exceptions.ResponseFormatError("'access_token' or 'uid' field not found")

            self._oauth_cred = OAuthCred(access_token, user_id)
            self._login = login

        except requests.HTTPError as e:
            raise exceptions.AuthenticationError("oauth token request error") from e

        except ValueError as e:
            raise exceptions.ResponseFormatError("response body format error") from e

    def logout(self) -> None:
        """
        Forget current user credentials.
        """

        self._oauth_cred = None
        self._login = None

    @property
    def is_authenticated(self) -> bool:
        """
        Checks if the client is authenticated.

        :return: `True` if the client is authenticated otherwise `False`
        """

        return all(self._oauth_cred)

    def auth_required(method: Callable):

        @ft.wraps(method)
        def decorator(self, *args, **kwargs):
            if not self.is_authenticated:
                raise exceptions.AuthenticationError("authentication required")

            return method(self, *args, **kwargs)

        return decorator

    def get_genres(self) -> List[Genre]:
        """
        Returns a list of available genres.

        :return: genre list
        """

        path = 'genres'
        resp = self._request('GET', self.API_HOST, path)

        return Result[List[Genre]].parse_obj(resp).result

    def get_playlists(self, *, user_id: Optional[int] = None) -> List[Playlist]:
        """
        Returns user's playlist list. If `user_id` argument is omitted current user id is used.

        :param user_id: user id
        :return: playlist list
        :rtype: `List[entities.Playlist]`
        """

        user_id = user_id or self._oauth_cred.user_id
        if not user_id:
            raise exceptions.AuthenticationError("authentication required")

        path = f'users/{user_id}/playlists/list'
        resp = self._request('GET', self.API_HOST, path)

        return Result[List[Playlist[TrackWrapper]]].parse_obj(resp).result

    def get_playlist(
        self,
        playlist_id: Optional[int] = None,
        *,
        title: Optional[str] = None,
        user_id: Optional[int] = None,
        rich_tracks: bool = False
    ) -> Union[Playlist[TrackWrapper], Playlist[Track]]:
        """
        Returns a playlist by id or title. If `user_id` argument is omitted current user id is used.

        :param playlist_id: playlist id
        :param title: playlist title
        :param user_id: user id
        :param rich_tracks: whether to add additional information to the tracks
        :return: requested playlist
        """

        assert (playlist_id or title) and not (playlist_id and title), "playlist_id ether title argument is required"

        user_id = user_id or self._oauth_cred.user_id
        if not user_id:
            raise exceptions.AuthenticationError("authentication required")

        if title:
            try:
                playlist = [playlist for playlist in self.get_playlists(user_id=user_id) if playlist.title == title][0]
            except IndexError:
                raise exceptions.NotFoundError("playlist '{}' not found".format(title))

            playlist_id = playlist.kind

        path = f'users/{user_id}/playlists'
        params = {
            'kinds': playlist_id,
            'rich-tracks': rich_tracks
        }
        resp = self._request('GET', self.API_HOST, path, params=params)

        playlist = Result[List[Playlist[TrackWrapper]]].parse_obj(resp).result[0]
        if rich_tracks:
            playlist.tracks = [track.unwrap() for track in playlist.tracks]

        return playlist

    @auth_required
    def create_playlist(self, title: str, *, visibility: Visibility = Visibility.PRIVATE) -> Playlist:
        """
        Creates a new playlist. Client should be authenticated on the service.

        :param title: playlist title
        :param visibility: playlist visibility
        :return: created playlist
        """

        path = f'users/{self._oauth_cred.user_id}/playlists/create'
        data = {
            'title': title,
            'visibility': visibility.name
        }
        resp = self._request('POST', self.API_HOST, path, data=data)

        return Result[Playlist[TrackWrapper]].parse_obj(resp).result

    @auth_required
    def delete_playlist(self, playlist_id: int) -> None:
        """
        Deletes playlist by an id. Client should be authenticated on the service.

        :param playlist_id: playlist id
        """

        path = f'users/{self._oauth_cred.user_id}/playlists/{playlist_id}/delete'
        self._request('POST', self.API_HOST, path)

    @auth_required
    def rename_playlist(self, playlist_id: int, *, title: str) -> None:
        """
        Renames playlist by an id. Client should be authenticated on the service.

        :param playlist_id: playlist id
        :param title: new title
        """

        path = f'users/{self._oauth_cred.user_id}/playlists/{playlist_id}/name'
        data = {
            'value': title,
        }

        self._request('POST', self.API_HOST, path, data=data)

    @auth_required
    def add_tracks_to_playlist(
        self,
        playlist_id: int,
        tracks: List[Union[TrackWrapper, Track]],
        *,
        at_position: int = 0,
        ignore_duplicates: bool = False
    ) -> None:
        """
        Adds tracks to a playlist. Client should be authenticated on the service.

        :param playlist_id: playlist id to add the tracks to
        :param tracks: track list to add to the playlist
        :param at_position: position to add tracks at
        :param ignore_duplicates: ignore duplicate tracks
        """

        path = f'users/{self._oauth_cred.user_id}/playlists/{playlist_id}/change-relative'

        playlist = self.get_playlist(playlist_id)
        if ignore_duplicates:
            tracks = set(tracks) - set(playlist.tracks)

        cur_revision = playlist.revision
        diff = [{
            'op': 'insert',
            'at': at_position,
            'tracks': [{
                'id': track.id,
                'albumid': track.album_id
            } for track in tracks]
        }]
        data = {
            'kind': playlist_id,
            'diff': json.dumps(diff, separators=(',', ':')),
            'revision': cur_revision
        }

        self._request('POST', self.API_HOST, path, data=data)

    @auth_required
    def delete_tracks_from_playlist(self, playlist_id: int, *, from_track: int, to_track: int) -> None:
        """
        Deletes tracks from the playlist. Client should be authenticated on the service.

        :param playlist_id: playlist id
        :param from_track: start position of the tracks to delete
        :param to_track: end position of the tracks to delete
        """

        path = f'users/{self._oauth_cred.user_id}/playlists/{playlist_id}/change-relative'

        playlist = self.get_playlist(playlist_id)
        cur_revision = playlist.revision

        diff = [{
            'op': 'delete',
            'from': from_track,
            'to': to_track
        }]
        data = {
            'kind': playlist_id,
            'diff': json.dumps(diff, separators=(',', ':')),
            'revision': cur_revision
        }

        self._request('POST', self.API_HOST, path, data=data)

    def search(self, query: str, *, search_type: SearchType = SearchType.ALL, page: int = 0) -> SearchResult:
        """
        Search for entities.

        :param query: query string
        :param search_type: search type
        :param page: result page number
        :return: search result
        """

        path = 'search'
        params = {
            'type': search_type.name,
            'text': query,
            'page': page
        }
        resp = self._request('GET', self.API_HOST, path, params=params)

        return Result[SearchResultWrapper].parse_obj(resp).result.unwrap()

    def search_artist(self, name: str, *, page: int = 0) -> List[Artist]:
        """
        Searches for artists with the requested name.

        :param name: artist name
        :param page: result page number
        :return: a list of the requested artists
        """

        return self.search(name, search_type=SearchType.ARTIST, page=page).artists

    def search_album(self, title: str, *, page: int = 0) -> List[Album]:
        """
        Searches for albums with the requested title.

        :param title: album title
        :param page: result page number
        :return: a list of the requested albums
        """

        return self.search(title, search_type=SearchType.ALBUM, page=page).albums

    def search_track(self, title: str, *, page: int = 0) -> List[Track]:
        """
        Searches for tracks with the requested title.

        :param title: track title
        :param page: result page number
        :return: a list of the requested tracks
        """

        return self.search(title, search_type=SearchType.TRACK, page=page).tracks

    def get_album(self, album_id: int) -> List[Album]:
        """
        Returns an album with `album_id` id

        :param album_id: album id
        :return: requested album
        """

        path = f'albums/{album_id}'
        resp = self._request('GET', self.API_HOST, path)

        return Result[Album].parse_obj(resp).result

    def get_similar_tracks(self, track_id: int) -> Similar:
        """
        Returns tracks similar to the track with `track_id` id

        :param track_id: track id
        :return: list of similar tracks
        """

        path = f'tracks/{track_id}/similar'
        resp = self._request('GET', self.API_HOST, path)

        return Result[Similar].parse_obj(resp).result
