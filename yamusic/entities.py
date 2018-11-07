import attr
import enum
from datetime import datetime
from typing import List, Optional


__all__ = [
    'Visability',
    'Sex',
    'SearchType',
    'Genre',
    'User',
    'Album',
    'Artist',
    'Track',
    'Playlist',
]


class Visability(enum.Enum):
    public = 0
    private = 1


class Sex(enum.Enum):
    unknown = 0
    male = 1
    female = 2


class SearchType(enum.Enum):
    all = 0
    artist = 1
    album = 2
    track = 3


@attr.s
class Genre(object):
    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    fullTitle   = attr.ib(type=str, cmp=False)
    tracksCount = attr.ib(type=str, cmp=False)

    def __str__(self):
        return self.title


@attr.s
class User(object):
    uid         = attr.ib(type=int, cmp=True)
    login       = attr.ib(type=str, cmp=False)
    name        = attr.ib(type=str, cmp=False)
    verified    = attr.ib(type=bool, cmp=False)
    sex         = attr.ib(type=Sex, cmp=False)

    def __str__(self):
        return "{} - '{}'".format(self.login, self.name)


@attr.s
class Album(object):
    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    year        = attr.ib(type=int, cmp=False)
    trackCount  = attr.ib(type=int, cmp=False)
    genre       = attr.ib(type=str, cmp=False)

    def __str__(self):
        return "{} ({})".format(self.title, self.year)


@attr.s
class Artist(object):
    id          = attr.ib(type=int, cmp=True)
    name        = attr.ib(type=str, cmp=False)
    composer    = attr.ib(type=bool, cmp=False)
    genres      = attr.ib(type=List[str], cmp=False)

    def __str__(self):
        return self.name


@attr.s
class Track(object):
    id          = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    durationMs  = attr.ib(type=int, cmp=False)
    albums      = attr.ib(type=List[Album], cmp=False)
    artists     = attr.ib(type=List[Artist], cmp=False)
    available   = attr.ib(type=bool, cmp=False)

    def __str__(self):
        return "{} - {} ({})".format(
            self.title, 
            ', '.join(str(artist) for artist in self.artists),
            ', '.join(str(album) for album in self.albums)
        )


@attr.s
class Playlist(object):
    kind        = attr.ib(type=int, cmp=True)
    title       = attr.ib(type=str, cmp=False)
    created     = attr.ib(type=datetime, cmp=False)
    modified    = attr.ib(type=datetime, cmp=False)
    trackCount  = attr.ib(type=int, cmp=False)
    durationMs  = attr.ib(type=int, cmp=False)
    visibility  = attr.ib(type=Visability, cmp=False)
    owner       = attr.ib(type=User, cmp=False)
    tracks      = attr.ib(type=Optional[List[Track]], cmp=False)
    revision    = attr.ib(type=int, cmp=False)

    def __str__(self):
        return "{} ({})".format(self.title, self.owner)

    def __iter__(self):
        return iter(self.tracks or [])
