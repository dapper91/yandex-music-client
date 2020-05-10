import datetime as dt
import enum
from typing import Iterator, List, Optional, Generic, TypeVar, Tuple

import pydantic as pd
from pydantic.generics import GenericModel


def to_camel(string: str) -> str:
    """
    Converts string to camel-case format.

    :param string: string to be camel-cased
    :return: camel-cased string
    """

    words = string.split('_')
    return ''.join(words[0] + word.capitalize() for word in words[1:])


class Visibility(enum.Enum):
    """
    Visibility.
    """

    PUBLIC = 'public'
    PRIVATE = 'private'


class Sex(enum.Enum):
    """
    Sex.
    """

    UNKNOWN = 'unknown'
    MALE = 'male'
    FEMALE = 'female'


class SearchType(enum.Enum):
    """
    Search type.
    """

    ALL = 'all'
    ARTIST = 'artist'
    ALBUM = 'album'
    TRACK = 'track'


class BaseModel(pd.BaseModel):
    """
    Package base model.
    """

    class Config:
        alias_generator = to_camel


ResultType = TypeVar('ResultType')


class Result(BaseModel, GenericModel, Generic[ResultType]):
    """
    Result wrapper.
    """

    result: ResultType


class Results(BaseModel, GenericModel, Generic[ResultType]):
    """
    Results wrapper.
    """

    results: ResultType


class Genre(BaseModel):
    """
    Music genre model.

    :param id: genre identifier
    :param title: genre title
    :param full_title: genre full title
    """

    id: str
    title: str
    full_title: Optional[str]

    def __str__(self) -> str:
        return self.title

    def __eq__(self, other) -> bool:
        if not isinstance(other, Genre):
            return NotImplemented

        return self.id == other.id


class User(BaseModel):
    """
    User model.

    :param uid: user identifier
    :param login: user login name
    :param sex: user sex
    :param verified: whether user is verified
    """

    uid: int
    login: str
    name: str
    sex: Sex
    verified: bool

    def __str__(self) -> str:
        return "{} - '{}'".format(self.login, self.name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.uid == other.uid


class Album(BaseModel):
    """
    Album model.

    :param id: album identifier
    :param title: album title
    :param track_count: album tracks count
    :param genre: album genre
    :param year: album recording year
    :param release_date: album release date
    """

    id: int
    title: str
    track_count: int

    genre: Optional[str]
    year: Optional[int]
    release_date: Optional[dt.datetime]

    def __str__(self) -> str:
        return "{} ({})".format(self.title, self.year)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Album):
            return NotImplemented

        return self.id == other.id


class Artist(BaseModel):
    """
    Artist model.

    :param id: artist identifier
    :param name: artist name
    :param composer: whether artist is a composer
    :param genres: artist genre list
    """

    id: int
    name: str
    composer: bool

    genres: List[str] = []

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Artist):
            return NotImplemented

        return self.id == other.id


class Track(BaseModel):
    """
    Audio track model.

    :param id: track identifier
    :param title: track title
    :param albums: track albums
    :param artists: track artists
    :param available: whether track available
    :param lyrics_available: whether lyrics available
    :param type: track type
    :param duration_ms: track duration
    :param real_id: track read id
    :param cover_uri: track cover url
    :param major: track major (label)
    :param files_size: track file size
    :param normalization: track audio normalization information
    """

    id: int
    title: str
    albums: List[Album]
    artists: List[Artist]
    available: bool
    lyrics_available: bool

    type: Optional[str]
    duration_ms: Optional[int]
    real_id: Optional[str]
    cover_uri: Optional[str]
    major: Optional[dict]
    files_size: Optional[int]
    normalization: Optional[dict]

    @property
    def album_id(self) -> int:
        """
        Returns track album identifier.
        """

        return self.albums[0].id

    @property
    def uid(self) -> Tuple[int, int]:
        """
        Playlist unique identifier.
        """

        return self.id, self.album_id

    def __str__(self) -> str:
        return "{} - {} ({})".format(
            self.title,
            ', '.join(str(artist) for artist in self.artists),
            ', '.join(str(album) for album in self.albums)
        )

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, other) -> bool:
        if not isinstance(other, Track):
            return NotImplemented

        return self.id == other.id


class TrackWrapper(BaseModel):
    """
    Audio track wrapper model. Contains

    :param id: track identifier
    :param album_id: track album identifier
    :param timestamp: track timestamp
    :param track: detailed track information
    """

    id: int
    album_id: Optional[int]
    timestamp: dt.datetime

    track: Optional[Track]

    @property
    def is_rich(self) -> bool:
        """
        Whether track wrapper is reach (contains detailed track information).
        """

        return self.track is not None

    @property
    def uid(self) -> Tuple[int, int]:
        """
        Playlist unique identifier.
        """

        return self.id, self.album_id

    def unwrap(self) -> Track:
        """
        Returns detailed track information if wrapper is reach, raise `ValueError` exception otherwise.
        """

        if not self.is_rich:
            raise ValueError("track is not rich")

        return self.track

    def __eq__(self, other) -> bool:
        if not isinstance(other, TrackWrapper):
            return NotImplemented

        return self.id == other.id and self.album_id == other.album_id


TrackType = TypeVar('TrackType')


class Similar(BaseModel, GenericModel, Generic[ResultType]):
    """
    Similar tracks request result.

    :param track: requested track
    :param similar_tracks: list of similar tracks
    """

    track: Track
    similar_tracks: List[Track]


class Playlist(BaseModel, GenericModel, Generic[TrackType]):
    """
    Music playlist model. Represents a collection of tracks plus some meta-information.

    :param kind: playlist identifier
    :param title: playlist title
    :param track_count: playlist track count
    :param owner: playlist owner
    :param tags: playlist tag list
    :param cover: playlist cover
    :param track_ids: playlist track id list
    :param duration: playlist duration
    :param tracks: playlist track list
    :param modified: playlist last modification time
    :param revision: playlist revision number (modification counter)
    :param visibility: whether playlist is visible
    :param likes_count: plyalsit likes count
    :param collective: whether playlist is collective
    """

    kind: int
    title: str
    track_count: int
    owner: User
    tags: List[dict] = []
    cover: dict
    track_ids: List[str] = []
    duration: int = 0

    tracks: Optional[List[TrackType]]
    modified: Optional[dt.datetime]
    revision: Optional[int]
    visibility: Optional[Visibility]
    likes_count: Optional[int]
    collective: Optional[bool]

    @property
    def uid(self) -> Tuple[int, int]:
        """
        Playlist unique identifier.
        """

        return self.kind, self.owner.uid

    def __str__(self) -> str:
        return "{} ({})".format(self.title, self.owner)

    def __iter__(self) -> Iterator[TrackType]:
        return iter(self.tracks or [])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Playlist):
            return NotImplemented

        return self.uid == other.uid


class SearchResult(BaseModel):
    """
    Search result.

    :param albums: list of found albums
    :param artists: list of found artists
    :param tracks: list of found tracks
    :param playlists: list of found playlists
    """

    albums: List[Album] = []
    artists: List[Artist] = []
    tracks: List[Track] = []
    playlists: List[Playlist[TrackWrapper]] = []

    def __str__(self):
        return "\n".join((
            f"found:",
            f"albums: {', '.join(map(str, self.albums))}",
            f"artists: {', '.join(map(str, self.artists))}",
            f"playlists: {', '.join(map(str, self.playlists))}",
            f"tracks: {', '.join(map(str, self.tracks))}",
        ))


class SearchResultWrapper(BaseModel):
    """
    Search result wrapper.
    """

    def unwrap(self) -> SearchResult:
        return SearchResult(
            albums=self.albums.results if self.albums else [],
            artists=self.artists.results if self.artists else [],
            playlists=self.playlists.results if self.playlists else [],
            tracks=self.tracks.results if self.tracks else [],
        )

    albums: Optional[Results[List[Album]]]
    artists: Optional[Results[List[Artist]]]
    tracks: Optional[Results[List[Track]]]
    playlists: Optional[Results[List[Playlist[TrackWrapper]]]]
