"""

This module uses and unofficial Yandex Music service api that has been grasped through some 
reverse engineering research which means it can be modified any time and the client would break down.

"""

from copy import deepcopy
import requests
import logging
import json
import re


class BaseError(Exception):
    """Base module exception"""


class ModelError(BaseError):
    """Model initialization error"""


class Property(object):
    def __init__(self, type, required=True, as_list=False, nullable=False, default=None):
        self.required = required
        self.default = default
        self.as_list = as_list
        self.nullable = nullable
        self.type = type


class ModelMeta(type):
    def __new__(mcs, *argc, **kwrags):
        cls = super().__new__(mcs, *argc, **kwrags)

        cls.__properties__ = mcs.get_properties(cls)
        cls.__attrs__ = []

        return cls

    def __call__(cls, arg=None, **kwrags):
        if arg is not None:
            if isinstance(arg, dict):
                return cls(**arg)
            elif isinstance(arg, cls):
                return deepcopy(arg)
            else:
                raise ModelError("invalid model initialization argument type: (expected: '{}' or 'dict', got '{}')"
                                 .format(cls.__name__, arg.__class__.__name__))
        else:
            return super().__call__(**kwrags)

    @staticmethod
    def get_properties(model):
        return [(name, getattr(model, name)) for name in dir(model) if isinstance(getattr(model, name), Property)]


class Model(object, metaclass=ModelMeta):
    def __init__(self, **kwrags):
        try:
            for name, prop in self.__properties__:
                try:
                    if prop.as_list:
                        value = [prop.type(item) for item in kwrags[name]]
                    else:
                        value = prop.type(kwrags[name])
                except KeyError:
                    if prop.default is not None:
                        value = prop.default
                    elif not prop.required:
                        value = None
                    else:
                        raise ModelError(
                            "model '{}' required property '{}' not found".format(self.__class__.__name__, name))
                except TypeError:
                    if prop.nullable and kwrags[name] is None:
                        value = prop.default
                    else:
                        raise

                self.__attrs__.append((name, value))
                setattr(self, name, value)

        except (ValueError, TypeError):
            raise ModelError("model '{}' property '{}' invalid format".format(self.__class__.__name__, name))

    def __repr__(self):
        return "<Model '{name}' ({properties})>".format(
            name=self.__class__.__name__,
            properties=", ".join(["{}={}".format(name, repr(prop)) for name, prop in self.__attrs__])
        )


class Artist(Model):
    id = Property(int, required=False)
    name = Property(str, required=True)

    def __str__(self):
        return "{name}".format(name=self.name)

    def __eq__(self, other):
        return self.id == other.id


class Album(Model):
    id = Property(int, required=False)
    title = Property(str, required=True)
    year = Property(int, required=True)

    def __str__(self):
        return "{title} [{year}]".format(title=self.title, year=self.year)

    def __eq__(self, other):
        return self.id == other.id


class Track(Model):
    id = Property(int, required=True)
    title = Property(str, required=False)
    duration = Property(int, required=False)
    size = Property(int, required=False)
    artists = Property(Artist, required=False, as_list=True, default=[])
    albums = Property(Album, required=False, as_list=True, default=[])

    def __str__(self):
        return "{title} - {artists} ({albums})".format(
            title=self.title,
            artists=", ".join([str(artist) for artist in self.artists]),
            albums=", ".join([str(album) for album in self.albums])
        )

    def __eq__(self, other):
        return self.id == other.id

    def to_dict(self):
        return {
            'title': self.title,
            'artists': [str(artist) for artist in self.artists],
            'albums': [str(album) for album in self.albums]
        }


class Playlist(Model):
    kind = Property(int, required=False)
    title = Property(str, required=True)
    description = Property(str, required=False, default='')
    revision = Property(int, required=False, nullable=True, default=0)
    trackCount = Property(int, required=True, default=0)
    tracks = Property(Track, required=False, as_list=True, default=[])

    def __str__(self):
        return "{title} ({trackCount})".format(title=self.title, trackCount=self.trackCount)

    def __eq__(self, other):
        return self.kind == other.kind

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'tracks': [track.to_dict() for track in self.tracks]
        }


class ArtistSearchResult(Model):
    items = Property(Artist, required=True, as_list=True)
    total = Property(int, required=False, default=0)


class AlbumSearchResult(Model):
    items = Property(Album, required=True, as_list=True)
    total = Property(int, required=False, default=0)


class PlaylistSearchResult(Model):
    items = Property(Playlist, required=True, as_list=True)
    total = Property(int, required=False, default=0)


class TracksSearchResult(Model):
    items = Property(Track, required=True, as_list=True)
    total = Property(int, required=False, default=0)


class SearchResult(Model):
    albums = Property(AlbumSearchResult, required=True)
    artists = Property(ArtistSearchResult, required=True)
    tracks = Property(TracksSearchResult, required=True)
    playlists = Property(PlaylistSearchResult, required=True)


def build_logger(level, format, file=None):
    loghandler = logging.FileHandler(file) if file else logging.StreamHandler()
    loghandler.setFormatter(logging.Formatter(format))
    logger = logging.getLogger('yamusic')
    logger.setLevel(level)
    logger.addHandler(loghandler)

    return logger


def build_url(host, path, proto='https'):
    return '{proto}://{host}/{path}'.format(host=host, path=path, proto=proto)


class ClientError(BaseError):
    """YaMusicClient base exception"""


class AuthError(ClientError):
    """Authentication error"""


class NotFoundError(ClientError, KeyError):
    """Requested object not found"""

    def __init__(self, msg, key):
        ClientError.__init__(self, msg)
        KeyError.__init__(self, key)


class YaMusicClient(object):
    LOGGER_DEFAULT_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
    LOGGER_DEFAULT_LOGLVL = logging.DEBUG

    API_HOST = 'music.yandex.ru'
    AUTH_HOST = 'passport.yandex.ru'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0',
        'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en,ru;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br'
    }

    def __init__(self, login, password, logger=None, remember_me=True):
        self.logger = logger.getChild('yamusic') if logger else build_logger(level=self.LOGGER_DEFAULT_LOGLVL,
                                                                             format=self.LOGGER_DEFAULT_FORMAT)

        self._username = login
        self._cookies = None

        self._auth(login, password, remember_me)

    def _auth(self, login, password, remember_me=True):
        # get cookies
        self._auth_step1(login, password, remember_me)

        # get sign key
        self._auth_step2()

    def _auth_step1(self, login, password, remember_me=True):
        """authenticates on passport.yandex.ru service and gets required cookies to get access to music.yandex.ru"""

        data = {
            'retpath': 'https://music.yandex.ru/home',
            'login': login,
            'passwd': password,
            'twoweeks': 'yes' if remember_me else 'no'
        }

        params = {
            'mode': 'embeddedauth'
        }

        resp = self._request('POST', self.AUTH_HOST, 'auth', params=params, headers=self.HEADERS, data=data,
                             allow_redirects=True)
        try:
            status = re.search('status=([\w-]+)', resp.headers['Location']).group(1)
        except (IndexError, AttributeError):
            raise AuthError("unknown authentication status")

        if status != 'ok':
            raise AuthError(status)

        self._cookies = resp.cookies

    def _auth_step2(self):
        """fetches a sign-key to sign some requests with (required for mutating operations like delete_playlist, add_tracks_to_playlist and etc.)"""

        resp = self._request('GET', self.API_HOST, 'home', headers=self.HEADERS)
        self._cookies = requests.cookies.merge_cookies(self._cookies, resp.cookies)

        try:
            self._sign_key = re.search('"sign":\s*"([\w:]+?)"', resp.text).group(1)
        except (IndexError, AttributeError):
            raise AuthError("a sign key can't be fetched")

    def _request(self, method, host, path, params=None, headers=None, data=None, **kwrags):
        try:
            headers = {**self.HEADERS, **{'Host': host}, **(headers or {})}
            url = build_url(host, path)

            self.logger.debug(
                "request (method: '{method}', url: '{url}', params: {params}, headers: {headers}, data: {data}, cookies: {cookies})"
                    .format(method=method, url=url, params=params, headers=headers, data=data, cookies=self._cookies))

            resp = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                cookies=self._cookies,
                **kwrags
            )

            self.logger.debug("response (code: {code}, headers: {headers}, body: '{body}')"
                              .format(code=resp.status_code, headers=resp.headers, body=None))

            resp.raise_for_status()

            return resp

        except requests.HTTPError as e:
            raise ClientError("http error: {}".format(e))

    def search(self, query, type='all', lang='en'):
        path = 'handlers/music-search.jsx'

        params = {
            'text': query,
            'type': type,
            'lang': lang
        }

        resp = self._request('GET', self.API_HOST, path, params).json()

        return SearchResult(resp)

    def search_artist(self, artist, lang='en'):
        artists = self.search('{}'.format(artist), 'artist', lang).artists.items

        return artists[0] if artists else None

    def search_album(self, artist, title, lang='en'):
        albums = self.search('{} - {}'.format(artist, title), 'album', lang).albums.items

        return albums[0] if albums else None

    def search_track(self, artist, title, lang='en'):
        tracks = self.search('{} - {}'.format(artist, title), 'track', lang).tracks.items

        return tracks[0] if tracks else None

    def get_playlists(self, lang='en'):
        path = 'handlers/library.jsx'

        params = {
            'owner': self._username,
            'filter': 'playlists',
            'lang': lang
        }

        resp = self._request('GET', self.API_HOST, path, params=params).json()

        return [Playlist(plist_dict) for plist_dict in resp['playlists']]

    def get_playlist_by_id(self, playlist_id):
        path = 'handlers/playlist.jsx'

        params = {
            'owner': self._username,
            'kinds': playlist_id
        }

        resp = self._request('GET', self.API_HOST, path, params=params).json()

        return Playlist(resp['playlist'])

    def get_playlist(self, title):
        try:
            return [playlist for playlist in self.get_playlists() if playlist.title == title][0]
        except IndexError:
            raise NotFoundError("playlist not found", title)

    def create_playlist(self, title, lang='en'):
        path = 'handlers/change-playlist.jsx'

        data = {
            'action': 'add',
            'title': title,
            'lang': lang,
            'sign': self._sign_key,
        }

        resp = self._request('POST', self.API_HOST, path, data=data).json()

        return Playlist(resp['playlist'])

    def rename_playlist_by_id(self, playlist_id, new_title, lang='en'):
        path = 'handlers/change-playlist.jsx'

        data = {
            'action': 'rename',
            'kind': playlist_id,
            'title': new_title,
            'lang': lang,
            'sign': self._sign_key
        }

        resp = self._request('POST', self.API_HOST, path, data).json()

        return Playlist(resp['playlist'])

    def rename_playlist(self, title, new_title, lang='en'):
        playlist = self.get_playlist(title)
        self.rename_playlist_by_id(playlist.kind, new_title, lang);

    def delete_playlist_by_id(self, playlist_id, lang='en'):
        path = 'handlers/change-playlist.jsx'

        data = {
            'action': 'delete',
            'kind': playlist_id,
            'lang': lang,
            'sign': self._sign_key
        }

        self._request('POST', self.API_HOST, path, data).json()

    def delete_playlist(self, title, lang='en'):
        playlist = self.get_playlist(title)
        self.delete_playlist_by_id(playlist.kind, lang)

    def add_tracks_to_playlist_by_id(self, playlist_id, tracks, at=0, prevent_dublicates=True):
        path = 'handlers/playlist-patch.jsx'

        playlist = self.get_playlist_by_id(playlist_id)

        cur_revision = playlist.revision

        diff = [{
            'op': 'insert',
            'at': at,
            'tracks': [{
                'id': track.id,
                'albumid': track.albums[0].id
            } for track in tracks if not (prevent_dublicates and track in playlist.tracks)]
        }]

        data = {
            'kind': playlist_id,
            'diff': json.dumps(diff, separators=(',', ':')),
            'revision': cur_revision,
            'sign': self._sign_key
        }

        resp = self._request('POST', self.API_HOST, path, data=data).json()

        return Playlist(resp['playlist'])

    def add_tracks_to_playlist(self, title, tracks, at=0, prevent_dublicates=True):
        playlist = self.get_playlist(title)
        return self.add_tracks_to_playlist_by_id(playlist.kind, tracks, at, prevent_dublicates)

    def remove_tracks_from_playlist_by_id(self, playlist_id, from_track=None, to_track=None):
        path = 'handlers/playlist-patch.jsx'

        playlist = self.get_playlist_by_id(playlist_id)

        cur_revision = playlist.revision
        tracks_count = len(playlist.tracks)

        diff = [{
            'op': 'delete',
            'from': from_track or 0,
            'to': to_track or tracks_count - 1
        }]

        data = {
            'kind': playlist_id,
            'diff': json.dumps(diff, separators=(',', ':')),
            'revision': cur_revision,
            'sign': self._sign_key
        }

        resp = self._request('POST', self.API_HOST, path, data=data).json()

        return Playlist(resp['playlist'])

    def remove_tracks_from_playlist(self, title, from_track=None, to_track=None):
        playlist = self.get_playlist(title)
        return self.remove_tracks_from_playlist_by_id(playlist.kind, from_track, to_track)
