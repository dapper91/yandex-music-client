"""
Yandex music service client.
"""

import functools
import json
import requests
import uuid

from . import entities
from . import exceptions
from . import logger
from . import schemas


def build_url(host, path, proto='https'):
    """
    Builds URL based on the parameters.

    :param host: URL hostname
    :param path: URL path
    :param proto: URL protocol
    :return: URL string
    """

    return '{proto}://{host}/{path}'.format(host=host, path=path, proto=proto)


def generate_uuid():
    """
    :return: unique UUID string
    """

    return str(uuid.uuid4()).replace('-', '')


class YaMusicClient(object):
    """
    A Yandex music service client. Creates a client instance and authenticates
    on the service if login and password are provided.

    :param login: yandex account user name
    :param password: yandex account password
    :param device_id: local device id (will be automatically generated if ommited)
    :param uuid: unique identifier (will be automatically generated if ommited)
    :param auth_data: authentication data, (access_token, user_id) pair
    """

    OAUTH_CLIENT_ID = '23cabbbdc6cd418abb4b39c32c41195d'
    OAUTH_CLIENT_SECRET = '53bc75238f0c4d08a118e51fe9203300'

    OAUTH_HOST = 'oauth.mobile.yandex.net'
    API_HOST = 'api.music.yandex.net'

    PACKAGE_NAME = 'ru.yandex.music'

    def __init__(self, login=None, password=None, device_id=None, uuid=None, auth_data=None):
        self._logger = logger.getChild(self.__class__.__name__)
        self._login = login
        self._device_id = device_id or generate_uuid()
        self._uuid = uuid or generate_uuid()
        self._access_token, self._user_id = auth_data or (None, None)

        if password is not None and login is not None:
            self.auth(login, password)

    def _request(self, method, host, path, params=None, headers=None, data=None, **kwrags):
        if self._access_token:
            headers = {**{'Authorization': 'OAuth ' + self._access_token}, **(headers or {})}

        resp = requests.request(
            method=method,
            url=build_url(host, path),
            params=params,
            headers=headers,
            data=data,
            **kwrags
        )
        resp.raise_for_status()
        return resp

    def auth(self, login, password):
        """
        Authenticates on the service as a `login` user.

        :param login: yandex account user name
        :param password: yandex account password
        :raises `exceptions.AuthenticationError`: if the credentials are not valid
        """

        self._login = login

        params = {
            'device_id':        self._device_id,
            'uuid':             self._uuid,
            'package_name':     self.PACKAGE_NAME
        }
        data = {
            'grant_type':       'password',
            'username':         login,
            'password':         password,
            'client_id':        self.OAUTH_CLIENT_ID,
            'client_secret':    self.OAUTH_CLIENT_SECRET
        }

        try:
            resp = self._request('POST', self.OAUTH_HOST, '1/token', params=params, data=data).json()
            self._access_token, self._user_id = resp.get('access_token'), resp.get('uid')

            if self._access_token is None or self._user_id is None:
                raise exceptions.ResponseFormatError("'access_token' or 'uid' field not found")

        except requests.HTTPError as e:
            raise exceptions.AuthenticationError("oauth token request error") from e

        except ValueError as e:
            raise exceptions.ResponseFormatError("response body format error") from e

    @property
    def is_authenticated(self):
        """
        Check if the user is authenticated.

        :return: `True` if the user is authenticated otherwise `False`
        """

        return self._access_token is not None and self._user_id is not None

    def auth_required(method):
        @functools.wraps(method)
        def decorator(self, *args, **kwargs):
            if not self.is_authenticated:
                raise exceptions.AuthenticationError("Authentication required")

            return method(self, *args, **kwargs)

        return decorator

    def get_genres(self):
        """
        Returns a list of the available genres.

        :return: genre list
        :rtype: `List[entities.Genre]`
        """

        path = 'genres'
        resp = self._request('GET', self.API_HOST, path)

        return schemas.GenreSchema(many_envelope='result', many=True).loads(resp.text).data

    def get_playlists(self, user_id=None):
        """
        Returns user's playlist list. If `user_id` argument is ommited current user id is used.

        :param user_id: user id
        :return: playlist list
        :rtype: `List[entities.Playlist]`
        """

        user_id = user_id or self._user_id
        path = 'users/{user_id}/playlists/list'.format(user_id=user_id)
        resp = self._request('GET', self.API_HOST, path)

        return schemas.PlaylistSchema(many_envelope='result', many=True).loads(resp.text).data

    def get_playlist(self, playlist_id, user_id=None, rich_tracks=True):
        """
        Returns a user's playlist by id. If `user_id` argument is ommited current user id is used.

        :param playlist_id: playlist id
        :param user_id: user id
        :param rich_tracks: whether to add additional information to tracks
        :return: the requested playlist
        :rtype: `entities.Playlist`
        """

        user_id = user_id or self._user_id
        path = 'users/{user_id}/playlists'.format(user_id=user_id)
        params = {
            'kinds': playlist_id,
            'rich-tracks': rich_tracks
        }
        resp = self._request('GET', self.API_HOST, path, params=params)

        return schemas.PlaylistSchema(many_envelope='result', many=True).loads(resp.text).data[0]

    def get_playlist_by_title(self, title, user_id=None):
        """
        Returns a user's playlist by title. If `user_id` argument is ommited current user id is used.

        :param title: playlist title
        :param user_id: user id
        :return: the requested playlist
        :rtype: `entities.Playlist`
        """

        playlists = [playlist for playlist in self.get_playlists() if playlist.title == title]
        try:
            playlist = playlists[0]
        except IndexError:
            raise exceptions.NotFoundError("playlist '{}' not found".format(title))

        return self.get_playlist(playlist.kind, user_id)

    @auth_required
    def create_playlist(self, title, visibility=entities.Visibility.private):
        """
        Creates a new playlist. Client should be authenticated on the service.

        :param title: new playlist title
        :param visibility: new playlist visibility
        :return: the created playlist
        :rtype: `entities.Playlist`
        """

        path = 'users/{user_id}/playlists/create'.format(user_id=self._user_id)
        data = {
            'title': title,
            'visibility': visibility.name
        }
        resp = self._request('POST', self.API_HOST, path, data=data)

        return schemas.PlaylistSchema(envelope='result').loads(resp.text).data

    @auth_required
    def delete_playlist(self, playlist_id):
        """
        Deletes playlist by id. Client should be authenticated on the service.

        :param playlist_id: playlist id
        """

        path = 'users/{user_id}/playlists/{playlist_id}/delete'.format(user_id=self._user_id, playlist_id=playlist_id)
        self._request('POST', self.API_HOST, path)

    @auth_required
    def rename_playlist(self, playlist_id, title):
        """
        Renames playlist by id. Client should be authenticated on the service.

        :param playlist_id: playlist id
        :param title: new title
        """

        path = 'users/{user_id}/playlists/{playlist_id}/name'.format(user_id=self._user_id, playlist_id=playlist_id)
        data = {
            'value': title,
        }

        self._request('POST', self.API_HOST, path, data=data)

    @auth_required
    def add_tracks_to_playlist(self, playlist_id, tracks, at_position=0, ignore_duplicates=False):
        """
        Adds tracks to the playlist. Client should be authenticated on the service.

        :param playlist_id: playlist id to add the tracks to
        :param tracks: track list to add to the playlist
        :param at_position: position to add tracks at
        :param ignore_duplicates: ignore duplicate tracks
        """

        path = 'users/{user_id}/playlists/{playlist_id}/change-relative'.format(user_id=self._user_id, playlist_id=playlist_id)

        playlist = self.get_playlist(playlist_id)
        if ignore_duplicates:
            tracks = set(tracks) - set(playlist.tracks)

        cur_revision = playlist.revision
        diff = [{
            'op': 'insert',
            'at': at_position,
            'tracks': [{
                'id': track.id,
                'albumid': track.albums[0].id
            } for track in tracks]
        }]
        data = {
            'kind': playlist_id,
            'diff': json.dumps(diff, separators=(',', ':')),
            'revision': cur_revision
        }

        self._request('POST', self.API_HOST, path, data=data)

    @auth_required
    def delete_tracks_from_playlist(self, playlist_id, from_track, to_track):
        """
        Deletes tracks from the playlist. Client should be authenticated on the service.

        :param playlist_id: playlist id
        :param from_track: start position of the tracks to delete
        :param to_track: end position of the tracks to delete
        """

        path = 'users/{user_id}/playlists/{playlist_id}/change-relative'.format(user_id=self._user_id, playlist_id=playlist_id)

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

    def search(self, query, search_type=entities.SearchType.all, page=0):
        """
        Makes a search query.

        :param query: query string
        :param search_type: search type (`SearchType.all`, `SearchType.artist`, `SearchType.album`, `SearchType.track`)
        :param page: result page number
        :return: the search result
        :rtype: `SearchResult`
        """

        path = 'search'
        params = {
            'type': search_type.name,
            'text': query,
            'page': page
        }
        resp = self._request('GET', self.API_HOST, path, params=params)

        return schemas.SearchResultSchema(many_envelope='result').loads(resp.text).data

    def search_artist(self, name, page=0):
        """
        Searches for the artist with name `name`.

        :param name: artist name
        :param page: result page number
        :return: a list of the requested artists
        :rtype: `List[entities.Artist]`
        """

        return self.search(name, entities.SearchType.artist, page).artists

    def search_album(self, title, page=0):
        """
        Searches for the album with title `title`.

        :param title: album title
        :param page: result page number
        :return: a list of the requested albums
        :rtype: `List[entities.Album]`
        """

        return self.search(title, entities.SearchType.album, page).albums

    def search_track(self, title, page=0):
        """
        Searches for the track with title `title`.

        :param title: track title
        :param page: result page number
        :return: a list of the requested tracks
        :rtype: `List[entities.Track]`
        """

        return self.search(title, entities.SearchType.track, page).tracks

    def get_album(self, album_id):
        """
        Returns the album with `album_id` id

        :param album_id: album id
        :return: the requested album
        :rtype: `entities.Album`
        """

        path = 'albums/{album_id}'.format(album_id=album_id)
        resp = self._request('GET', self.API_HOST, path)

        return schemas.AlbumSchema(envelope='result').loads(resp.text).data

    def get_similar_tracks(self, track_id):
        """
        Returns tracks similar to the track with `track_id` id

        :param track_id: track id
        :return: list of similar tracks
        :rtype: `List[entities.Track]`
        """

        path = 'tracks/{track_id}/similar'.format(track_id=track_id)
        resp = self._request('GET', self.API_HOST, path)

        return schemas.TrackSchema(many_envelope='result', envelope='track').loads(resp.text).data
