"""
Service entities serialization schemas.
"""

import marshmallow as mm
import marshmallow.exceptions as mme

from . import entities
from . import exceptions

__all__ = [
    'BaseSchema',
    'GenreSchema',
    'UserSchema',
    'ArtistSchema',
    'AlbumSchema',
    'TrackSchema',
    'PlaylistSchema',
    'SearchResultSchema',
]


class EnumField(mm.fields.Field):
    """
    Serializable enum field.
    """

    def __init__(self, enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enum = enum

    def _serialize(self, value, attr, obj, **kwargs):
        return self._enum.name

    def _deserialize(self, value, attr, data, **kwargs):
        return self._enum[value]


class BaseSchema(mm.Schema):
    """
    Base serialization schema. All schemas should be inherited from it.
    """

    __object__ = None

    def __init__(self, *args, envelope=None, many_envelope=None, **kwargs):
        """
        :param args: positional arguments to be passed to `marshmallow.Schema`
        :param envelope: field that contains an object data
        :param many_envelope: field that contains a list of object if `many` argument is `True`
        :param kwargs: named arguments to be passed to `marshmallow.Schema`
        """

        super().__init__(self, *args, **kwargs)
        self.__envelope = {
            'one': envelope,
            'many': many_envelope
        }

    def _unwrap_envelope(self, data, envelope):
        key = self.__envelope[envelope]
        if key is not None:
            try:
                data = data[key]
            except KeyError:
                raise mme.ValidationError("required field '{}' is missing".format(key))

        return data

    @mm.pre_load(pass_many=False)
    def unwrap_envelope(self, data):
        return self._unwrap_envelope(data, 'one')

    @mm.pre_load(pass_many=True)
    def unwrap_envelope_many(self, data, many):
        return self._unwrap_envelope(data, 'many')

    @mm.post_load
    def build_object(self, data):
        if self.__object__ is None:
            name = self.__class__.__name__
            if name.endswith('Schema'):
                name = name[:-6]
            else:
                name += 'Object'

            obj = type(name, (object,), data)
        else:
            obj = self.__object__(**data)

        return obj

    def handle_error(self, error, data):
        raise exceptions.ResponseFormatError(error)


class GenreSchema(BaseSchema):
    """
    Genre entity serialization schema.
    """

    __object__  = entities.Genre

    id          = mm.fields.Str(required=True)
    title       = mm.fields.Str(required=True)
    fullTitle   = mm.fields.Str(required=False, missing='')
    tracksCount = mm.fields.Int(required=True)


class UserSchema(BaseSchema):
    """
    User entity serialization schema.
    """

    __object__  = entities.User

    uid         = mm.fields.Int(required=True)
    login       = mm.fields.Str(required=True)
    name        = mm.fields.Str(required=True)
    verified    = mm.fields.Bool(required=True)
    sex         = EnumField(entities.Sex, required=True)


class AlbumSchema(BaseSchema):
    """
    Album entity serialization schema.
    """

    __object__  = entities.Album

    id          = mm.fields.Int(required=True)
    title       = mm.fields.Str(required=True)
    year        = mm.fields.Int(missing=None)
    releaseDate = mm.fields.DateTime(required=False, missing=None)
    trackCount  = mm.fields.Int(required=True)
    genre       = mm.fields.Str(required=False, missing=None)


class ArtistSchema(BaseSchema):
    """
    Artist entity serialization schema.
    """

    __object__  = entities.Artist

    id          = mm.fields.Int(required=True)
    name        = mm.fields.Str(required=True)
    composer    = mm.fields.Bool(required=True)
    genres      = mm.fields.List(mm.fields.Str(), required=False, missing=[])


class TrackSchema(BaseSchema):
    """
    Track entity serialization schema.
    """

    __object__  = entities.Track

    id          = mm.fields.Int(required=True)
    title       = mm.fields.Str(required=True)
    durationMs  = mm.fields.Int(missing=0)
    albums      = mm.fields.Nested(AlbumSchema(many=True), required=True)
    artists     = mm.fields.Nested(ArtistSchema(many=True), required=True)
    available   = mm.fields.Bool(required=True)


class PlaylistSchema(BaseSchema):
    """
    Playlist entity serialization schema.
    """

    __object__  = entities.Playlist

    title       = mm.fields.Str(required=True)
    kind        = mm.fields.Int(required=True)
    created     = mm.fields.DateTime(required=False, missing=None)
    modified    = mm.fields.DateTime(required=False, missing=None)
    trackCount  = mm.fields.Int(required=True)
    durationMs  = mm.fields.Int(required=False, missing=None)
    visibility  = EnumField(entities.Visibility, required=False, missing=None)
    owner       = mm.fields.Nested(UserSchema, required=True)
    tracks      = mm.fields.Nested(TrackSchema(envelope='track', many=True), missing=None)
    revision    = mm.fields.Int(required=False, missing=None)


class SearchResultSchema(BaseSchema):
    """
    Search result entity serialization schema.
    """

    albums      = mm.fields.Nested(AlbumSchema(many_envelope='results', many=True), required=False, missing={'results': []})
    artists     = mm.fields.Nested(ArtistSchema(many_envelope='results', many=True), required=False, missing={'results': []})
    playlists   = mm.fields.Nested(PlaylistSchema(many_envelope='results', many=True), required=False, missing={'results': []})
    tracks      = mm.fields.Nested(TrackSchema(many_envelope='results', many=True), required=False, missing={'results': []})
