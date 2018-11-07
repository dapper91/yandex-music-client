from marshmallow import Schema, fields, pre_load, post_load
from marshmallow.exceptions import ValidationError

from .entities import *
from .exceptions import ResponseFormatError


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


class EnumField(fields.Field):

    def __init__(self, enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enum = enum

    def _serialize(self, value, attr, obj, **kwargs):
        return self._enum.name

    def _deserialize(self, value, attr, data, **kwargs):
        return self._enum[value]


class BaseSchema(Schema):

    __object__ = None

    def __init__(self, *args, envelope=None, many_envelope=None, **kwargs):
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
                raise ValidationError("required field '{}' is missing".format(key))
        
        return data

    @pre_load(pass_many=False)
    def unwrap_envelope(self, data):
        return self._unwrap_envelope(data, 'one')

    @pre_load(pass_many=True)
    def unwrap_envelope_many(self, data, many):
        return self._unwrap_envelope(data, 'many')

    @post_load
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
        raise ResponseFormatError(error)


class GenreSchema(BaseSchema):

    __object__  = Genre

    id          = fields.Str(required=True)
    title       = fields.Str(required=True)
    fullTitle   = fields.Str(required=False, missing='')
    tracksCount = fields.Int(required=True)


class UserSchema(BaseSchema):

    __object__  = User

    uid         = fields.Int(required=True)
    login       = fields.Str(required=True)
    name        = fields.Str(required=True)
    verified    = fields.Bool(required=True)
    sex         = EnumField(Sex, required=True)


class AlbumSchema(BaseSchema):

    __object__  = Album

    id          = fields.Int(required=True)
    title       = fields.Str(required=True)
    year        = fields.Int(missing=None)
    trackCount  = fields.Int(required=True)
    genre       = fields.Str(required=False, missing=None)


class ArtistSchema(BaseSchema):

    __object__  = Artist

    id          = fields.Int(required=True)
    name        = fields.Str(required=True)
    composer    = fields.Bool(required=True)
    genres      = fields.List(fields.Str(), required=False, missing=[])


class TrackSchema(BaseSchema):

    __object__  = Track

    id          = fields.Int(required=True)
    title       = fields.Str(required=True)
    durationMs  = fields.Int(missing=0)
    albums      = fields.Nested(AlbumSchema(many=True), required=True)
    artists     = fields.Nested(ArtistSchema(many=True), required=True)
    available   = fields.Bool(required=True)


class PlaylistSchema(BaseSchema):

    __object__  = Playlist

    title       = fields.Str(required=True)
    kind        = fields.Int(required=True)
    created     = fields.DateTime(required=False, missing=None)
    modified    = fields.DateTime(required=False, missing=None)
    trackCount  = fields.Int(required=True)
    durationMs  = fields.Int(required=False, missing=None)
    visibility  = EnumField(Visability, required=False, missing=None)
    owner       = fields.Nested(UserSchema, required=True)
    tracks      = fields.Nested(TrackSchema(envelope='track', many=True), missing=None)
    revision    = fields.Int(required=False, missing=None)


class SearchResultSchema(BaseSchema):
    albums      = fields.Nested(AlbumSchema(many_envelope='results', many=True), required=False, missing={'results': []})
    artists     = fields.Nested(ArtistSchema(many_envelope='results',many=True), required=False, missing={'results': []})
    playlists   = fields.Nested(PlaylistSchema(many_envelope='results',many=True), required=False, missing={'results': []})
    tracks      = fields.Nested(TrackSchema(many_envelope='results',many=True), required=False, missing={'results': []})
