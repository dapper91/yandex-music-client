"""
Yandex music client library.
"""

from yamusic.client import YaMusicClient, OAuthCred
from yamusic.models import (
    Album,
    Artist,
    Genre,
    Playlist,
    SearchResult,
    SearchType,
    Sex,
    Similar,
    Track,
    TrackWrapper,
    User,
    Visibility,
)

__all__ = [
    '__title__',
    '__summary__',
    '__uri__',
    '__version__',
    '__author__',
    '__email__',
    '__license__',

    'YaMusicClient',
    'OAuthCred',

    'Album',
    'Artist',
    'Genre',
    'Playlist',
    'SearchResult',
    'SearchType',
    'Sex',
    'Similar',
    'Track',
    'TrackWrapper',
    'User',
    'Visibility',
]


__title__ = "yamusic"
__summary__ = "Yandex Music service library."
__uri__ = "https://github.com/dapper91/yandex-music-client"

__version__ = "1.0.0"

__author__ = "Dmitry Pershin"
__email__ = "dapper91@mail.ru"

__license__ = "Public Domain License"
