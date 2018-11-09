from uuid import uuid4
import json
import requests

from .schemas import *
from .entities import *
from .exceptions import AuthenticationError, ResponseFormatError, NotFoundError
from . import logger


def build_url(host, path, proto='https'):
    return '{proto}://{host}/{path}'.format(host=host, path=path, proto=proto)

def generate_uuid():
    return str(uuid4()).replace('-', '')


class YaMusicClient(object):

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
            resp = self._request('POST', self.OAUTH_HOST, '1/token', params=params, data=data)
            self._access_token, self._user_id = resp.get('access_token'), resp.get('uid')
            
            if self._access_token is None or self._user_id is None:
                raise ResponseFormatError("'access_token' or 'uid' field not found")

        except requests.HTTPError as e:
            raise AuthenticationError("oauth token request error") from e

    @property
    def is_authenticated(self):
        return self._access_token is not None and self._user_id is not None

    def get_genres(self):
        path = 'genres'

        resp = self._request('GET', self.API_HOST, path)

        return GenreSchema(many_envelope='result', many=True).loads(resp.text).data

    def get_playlists(self, user_id=None):
        user_id = user_id or self._user_id
        path = 'users/{user_id}/playlists/list'.format(user_id=user_id)

        resp = self._request('GET', self.API_HOST, path)

        return PlaylistSchema(many_envelope='result', many=True).loads(resp.text).data

    def get_playlist(self, playlist_id, user_id=None, rich_tracks=True):
        user_id = user_id or self._user_id
        path = 'users/{user_id}/playlists'.format(user_id=user_id)

        params = {
            'kinds': playlist_id,
            'rich-tracks': rich_tracks
        }

        resp = self._request('GET', self.API_HOST, path, params=params)

        return PlaylistSchema(many_envelope='result', many=True).loads(resp.text).data[0]

    def get_playlist_by_title(self, title, user_id=None):
        playlists = [playlist for playlist in self.get_playlists() if playlist.title == title]
        try:
            playlist = playlists[0]
        except IndexError:
            raise NotFoundError("playlist '{}' not found".format(title))

        return self.get_playlist(playlist.kind, user_id)

    def create_playlist(self, title, visibility=Visability.private):
        path = 'users/{user_id}/playlists/create'.format(user_id=self._user_id)

        data = {
            'title': title,
            'visibility': visibility.name
        }

        resp = self._request('POST', self.API_HOST, path, data=data)

        return PlaylistSchema(envelope='result').loads(resp.text).data

    def delete_playlist(self, playlist_id):
        path = 'users/{user_id}/playlists/{playlist_id}/delete'.format(user_id=self._user_id, playlist_id=playlist_id)

        self._request('POST', self.API_HOST, path)

    def rename_playlist(self, playlist_id, title):
        path = 'users/{user_id}/playlists/{playlist_id}/name'.format(user_id=self._user_id, playlist_id=playlist_id)

        data = {
            'value': title,
        }

        self._request('POST', self.API_HOST, path, data=data)

    def add_tracks_to_playlist(self, playlist_id, tracks, at_position=0, ignore_dublicates=False):
        path = 'users/{user_id}/playlists/{playlist_id}/change-relative'.format(user_id=self._user_id, playlist_id=playlist_id)
        
        playlist = self.get_playlist(playlist_id)

        if ignore_dublicates:
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


    def delete_tracks_from_playlist(self, playlist_id, from_track, to_track):
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

    def search(self, query, search_type=SearchType.all, page = 0):
        path = 'search'

        params = {
            'type': search_type.name,
            'text': query,
            'page': 0
        }

        resp = self._request('GET', self.API_HOST, path, params=params)

        return SearchResultSchema(many_envelope='result').loads(resp.text).data

    def search_artist(self, name, page=0):
        return self.search(name, SearchType.artist, page).artists

    def search_album(self, title, page=0):
        return self.search(title, SearchType.album, page).albums

    def search_track(self, title, page=0):
        return self.search(title, SearchType.track, page).tracks

    def get_album(self, album_id, with_tracks=False):
        path = 'albums/{album_id}'.format(album_id=album_id)

        resp = self._request('GET', self.API_HOST, path)

        return AlbumSchema(envelope='result').loads(resp.text).data

    def get_similar_tracks(self, track_id):
        path = 'tracks/{track_id}/similar'.format(track_id=track_id)

        resp = self._request('GET', self.API_HOST, path)

        return TrackSchema(many_envelope='result', envelope='track').loads(resp.text).data
