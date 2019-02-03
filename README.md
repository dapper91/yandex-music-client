
# Yandex Music client

A python3 Yandex Music (https://music.yandex.ru) Library.

This library doesn't provide an ability to download or listen audio tracks bypassing the
official audio players, which violates the user agreements (https://yandex.ru/legal/music_termsofuse/). 
The purpose of the library is to provide a sufficient way of managing your audio tracks, backup your 
playlists, import/export your playlists from/to your local audio library or other music services 
like Spotify, Apple Music and so on.

The library uses OAuth 2.0 protocol (https://oauth.net/2/) password grant type for the authentication, 
which means it doesn't store your password, instead it fetches a temporary token granted to access only
your yandex music service data so that it doesn't jeopardize your privacy.

**NB**: This module uses an unofficial Yandex Music service api that has been grasped through some 
reverse engineering research which means it can be modified any time and the client would break down.

## Dependencies

* requests (http://docs.python-requests.org)
* marshmallow (https://marshmallow.readthedocs.io)
* attrs (https://www.attrs.org)


## Usage example

```python

from yamusic import YaMusicClient


client = YaMusicClient('user', 'password')

print("User playlists:")
for playlist in client.get_playlists():
    print("{title} ({track_count})".format(
        title=playlist.title, 
        track_count=playlist.trackCount)
    )



playlist_name = 'Folk'
print("{} playlist:".format(playlist_name))

for track in client.get_playlist_by_title(playlist_name).tracks:
    print("\t{title} - {authors} ({albums})".format(
        title=track.title, 
        authors=', '.join(track.authors), 
        albums=', '.join(track.albums))
    )



playlist = client.create_playlist('Russian Rock')

tracks = [
    client.search_track('{} - {}'.format(artist_name, track_name))[0] for artist_name, track_name in [
        ('ДДТ',  'В последнюю осень'), 
        ('Ария', 'Я здесь'), 
        ('Кино', 'Хочу перемен'), 
        ('ДДТ',  'Просвистела'),
        ('ДДТ',  'Просвистела')
    ]
]
    
client.add_tracks_to_playlist(playlist.kind, tracks, ignore_dublicates=True)

```


## API

### yamusic.client.Client

**\_\_init__(login=None, password=None, device_id=None, uuid=None, auth_data=None)**

Creates a client instance and authenticates on the service if `login` and `password` are provided.

*Parameters*:

- `login` - yandex account user name
- `password` - yandex account password
- `device_id` - local device id (will be automatically generated if ommited)
- `uuid` - unique identifier (will be automatically generated if ommited)
- `auth_data` - authentication data, (access_token, user_id) pair

**auth(login, password)**

Authenticates on the service as a `login` user.

*Parameters*:

- `login` - yandex account user name
- `password` - yandex account password

**is_authenticated**

Check if the user is authenticated.

*Returns*: `True` if the user is authenticated otherwise `False`.

*Return type*: `bool`

**get_genres()**

Returns the available genres list.

*Returns*: The genres list.

*Return type*: `Genre`

**get_playlists(user_id=None)**

Returns user's playlist list. If `user_id` argument is ommited current user_id is used. If user is not authenticated AttributError is raised.

*Returns*: The genres list.

*Return type*: `List[Playlist]`

**get_playlist_by_title(self, title, user_id=None)**

Returns a playlist with tittle `title` for user `user_id`. If `user_id` is ommited current user id is used.

*Parameters*:

- `title` - playlist title
- `user_id` - user id

*Returns*: Playlist with title `title`.

*Return type*: `Playlist`

**create_playlist(self, title, visibility=entities.Visability.private)**

Creates playlist. Client should be authenticated on the service.

*Parameters*:

- `title` - playlist title
- `visability` - playlist visibility
   
**delete_playlist(self, playlist_id)**

Deletes playlist. Client should be authenticated on the service.

*Parameters*:

- `playlist_id` - playlist id to delete

**add_tracks_to_playlist(self, playlist_id, tracks, at_position=0, ignore_dublicates=False)**

*(empty)*

**delete_tracks_from_playlist(self, playlist_id, from_track, to_track)**

*(empty)*

**search(self, query, search_type=entities.SearchType.all, page = 0)**

*(empty)*

**search_artist(self, name, page=0)**

*(empty)*

**search_album(self, title, page=0)**

*(empty)*

**search_track(self, title, page=0)**

*(empty)*

**get_album(self, album_id, with_tracks=False)**

*(empty)*

**get_similar_tracks(self, track_id)**

*Parameters*:

- `track_id` - track id

*Returns*: Returns tracks similar to the track with id `track_id`.

*Return Type*: `List[Track]`

### yamusic.exceptions

**class BaseError(Exception)**

Base module exception.

**class AuthenticationError(BaseError)**

Raised when an authentication error occured (login or password are incorrect).

**class ResponseFormatError(BaseError)**

Raised when the response formant is incorrect. Typically indicates that the api data format has been changed.

**class NotFoundError(BaseError)**

Raised when the requested object not found.


## License

Unlicense
