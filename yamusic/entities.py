"""
Library types and entities.
"""

import attr
import datetime
import enum
import typing

__all__ = [
    'Visibility',
    'Sex',
    'SearchType',
    'Genre',
    'User',
    'Album',
    'Artist',
    'Track',
    'Playlist',
]


class Visibility(enum.Enum):
    """
    Visibility type enumeration.
    """

    public = 0
    private = 1


class Sex(enum.Enum):
    """
    Sex type enumeration.
    """

    unknown = 0
    male = 1
    female = 2


class SearchType(enum.Enum):
    """
    Search type enumeration.
    """

    all = 0
    artist = 1
    album = 2
    track = 3


@attr.s(frozen=True)
class Genre(object):
    """
    Music genre type.
    """

    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    fullTitle   = attr.ib(type=str, cmp=False)
    tracksCount = attr.ib(type=str, cmp=False)

    def __str__(self):
        return self.title


@attr.s(frozen=True)
class User(object):
    """
    User type.
    """

    uid         = attr.ib(type=int, cmp=True)
    login       = attr.ib(type=str, cmp=False)
    name        = attr.ib(type=str, cmp=False)
    verified    = attr.ib(type=bool, cmp=False)
    sex         = attr.ib(type=Sex, cmp=False)

    def __str__(self):
        return "{} - '{}'".format(self.login, self.name)


@attr.s(frozen=True)
class Album(object):
    """
    Album type.
    """

    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    year        = attr.ib(type=int, cmp=False)
    trackCount  = attr.ib(type=int, cmp=False)
    genre       = attr.ib(type=str, cmp=False)
    releaseDate = attr.ib(type=datetime.datetime, cmp=False)

    def __str__(self):
        return "{} ({})".format(self.title, self.year)


@attr.s(frozen=True)
class Artist(object):
    """
    Artist type.
    """

    id          = attr.ib(type=int, cmp=True)
    name        = attr.ib(type=str, cmp=False)
    composer    = attr.ib(type=bool, cmp=False)
    genres      = attr.ib(type=typing.List[str], cmp=False)

    def __str__(self):
        return self.name


@attr.s(frozen=True)
class Track(object):
    """
    Audio track type.
    """

    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    durationMs  = attr.ib(type=int, cmp=False)
    albums      = attr.ib(type=typing.List[Album], cmp=False)
    artists     = attr.ib(type=typing.List[Artist], cmp=False)
    available   = attr.ib(type=bool, cmp=False)

    def __str__(self):
        return "{} - {} ({})".format(
            self.title,
            ', '.join(str(artist) for artist in self.artists),
            ', '.join(str(album) for album in self.albums)
        )


@attr.s(frozen=True)
class Playlist(object):
    """
    Music playlist type. Represents a collection of tracks plus some metainformaion.
    """

    kind        = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    created     = attr.ib(type=datetime.datetime, cmp=False)
    modified    = attr.ib(type=datetime.datetime, cmp=False)
    trackCount  = attr.ib(type=int, cmp=False)
    durationMs  = attr.ib(type=int, cmp=False)
    visibility  = attr.ib(type=Visibility, cmp=False)
    owner       = attr.ib(type=User, cmp=False)
    tracks      = attr.ib(type=typing.Optional[typing.List[Track]], cmp=False)
    revision    = attr.ib(type=int, cmp=False)

    def __str__(self):
        return "{} ({})".format(self.title, self.owner)

    def __iter__(self):
        return iter(self.tracks or [])
