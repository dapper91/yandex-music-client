
# Yandex Music client

A python3 [Yandex Music](https://music.yandex.ru) service library.

This library doesn't provide an ability to download or listen audio tracks bypassing the
official audio players, which violates the [user agreements](https://yandex.ru/legal/music_termsofuse/). 
The purpose of the library is to provide a sufficient way of managing your audio tracks, backup your 
playlists, import/export your playlists from/to your local audio library or other music services 
like Spotify, Apple Music and so on.

The library uses [OAuth 2.0](https://oauth.net/2/) protocol password grant type for the authentication, 
which means it doesn't store your password, instead it fetches a temporary token granted to access only
your yandex music service data so that it doesn't jeopardize your privacy.

**NB**: This module uses an unofficial Yandex Music service api that has been grasped through some 
reverse engineering research which means it can be modified any time and the client would break down.

# Dependencies

* [requests](http://docs.python-requests.org)
* [marshmallow](https://marshmallow.readthedocs.io)
* [attrs](https://www.attrs.org)


# Usage example

### Playlists backup
```python

import getpass
import csv
import sys

from yamusic import client
from yamusic import exceptions


username = getpass.getuser()
username = input("Login ({}): ".format(username)) or username
password = getpass.getpass("Password: ")

print("Connecting to Yandex Music...")

try:
    ym_client = client.YaMusicClient(username, password)
except exceptions.AuthenticationError:
    print("Authentication error: username or password is incorrect")
    sys.exit(1)


with open('playlist-backup.csv', 'w', newline='') as backup_file:
    csv_writer = csv.DictWriter(backup_file, fieldnames=['playlist', 'artist', 'title', 'album'])
    csv_writer.writeheader()

    print("Downloading user's playlists...")

    for playlist in ym_client.get_playlists():
        print("Backing up '{}' playlist...".format(playlist.title))

        for track in ym_client.get_playlist(playlist.kind):
            csv_writer.writerow({
                'playlist': playlist.title,
                'artist': track.artists[0].name,
                'title': track.title,
                'album': track.albums[0].title if track.albums else '',
            })

```

### Playlists manipulation
```python

from yamusic.client import YaMusicClient


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
    
client.add_tracks_to_playlist(playlist.kind, tracks, ignore_duplicates=True)

```


# API

## yamusic.client

Yandex music service client.

### YaMusicClient
```python
YaMusicClient(self, login=None, password=None, device_id=None, uuid=None, auth_data=None)
```

A Yandex music service client. Creates a client instance and authenticates
on the service if login and password are provided.

**Arguments**:

- `login`: yandex account user name
- `password`: yandex account password
- `device_id`: local device id (will be automatically generated if ommited)
- `uuid`: unique identifier (will be automatically generated if ommited)
- `auth_data`: authentication data, (access_token, user_id) pair

### is_authenticated

Check if the user is authenticated.

**Returns**:

`True` if the user is authenticated otherwise `False`

### auth
```python
YaMusicClient.auth(self, login, password)
```

Authenticates on the service as a `login` user.

**Arguments**:

- `login`: yandex account user name
- `password`: yandex account password

**Raises**:

- ``exceptions.AuthenticationError``: if the credentials are not valid

### get_genres
```python
YaMusicClient.get_genres(self)
```

Returns a list of the available genres.

**Returns**:

genre list

**Return Type**:

`List[entities.Genre]`

### get_playlists
```python
YaMusicClient.get_playlists(self, user_id=None)
```

Returns user's playlist list. If `user_id` argument is ommited current user id is used.

**Arguments**:

- `user_id`: user id

**Returns**:

playlist list

**Return Type**:

`List[entities.Playlist]`

### get_playlist
```python
YaMusicClient.get_playlist(self, playlist_id, user_id=None, rich_tracks=True)
```

Returns a user's playlist by id. If `user_id` argument is ommited current user id is used.

**Arguments**:

- `playlist_id`: playlist id
- `user_id`: user id
- `rich_tracks`: whether to add additional information to tracks

**Returns**:

the requested playlist

**Return Type**:

`entities.Playlist`

### get_playlist_by_title
```python
YaMusicClient.get_playlist_by_title(self, title, user_id=None)
```

Returns a user's playlist by title. If `user_id` argument is ommited current user id is used.

**Arguments**:

- `title`: playlist title
- `user_id`: user id

**Returns**:

the requested playlist

**Return Type**:

`entities.Playlist`

### create_playlist
```python
YaMusicClient.create_playlist(self, title, visibility)
```

Creates a new playlist. Client should be authenticated on the service.

**Arguments**:

- `title`: new playlist title
- `visibility`: new playlist visibility

**Returns**:

the created playlist

**Return Type**:

`entities.Playlist`

### delete_playlist
```python
YaMusicClient.delete_playlist(self, playlist_id)
```

Deletes playlist by id. Client should be authenticated on the service.

**Arguments**:

- `playlist_id`: playlist id

### rename_playlist
```python
YaMusicClient.rename_playlist(self, playlist_id, title)
```

Renames playlist by id. Client should be authenticated on the service.

**Arguments**:

- `playlist_id`: playlist id
- `title`: new title

### add_tracks_to_playlist
```python
YaMusicClient.add_tracks_to_playlist(self, playlist_id, tracks, at_position=0, ignore_duplicates=False)
```

Adds tracks to the playlist. Client should be authenticated on the service.

**Arguments**:

- `playlist_id`: playlist id to add the tracks to
- `tracks`: track list to add to the playlist
- `at_position`: position to add tracks at
- `ignore_duplicates`: ignore duplicate tracks

### delete_tracks_from_playlist
```python
YaMusicClient.delete_tracks_from_playlist(self, playlist_id, from_track, to_track)
```

Deletes tracks from the playlist.

**Arguments**:

- `playlist_id`: playlist id
- `from_track`: start position of the tracks to delete
- `to_track`: end position of the tracks to delete

### search
```python
YaMusicClient.search(self, query, search_type, page=0)
```

Makes a search query.

**Arguments**:

- `query`: query string
- `search_type`: search type (`SearchType.all`, `SearchType.artist`, `SearchType.album`, `SearchType.track`)
- `page`: result page number

**Returns**:

the search result

**Return Type**:

`SearchResult`

### search_artist
```python
YaMusicClient.search_artist(self, name, page=0)
```

Searches for the artist with name `name`.

**Arguments**:

- `name`: artist name
- `page`: result page number

**Returns**:

a list of the requested artists

**Return Type**:

`List[entities.Artist]`

### search_album
```python
YaMusicClient.search_album(self, title, page=0)
```

Searches for the album with title `title`.

**Arguments**:

- `title`: album title
- `page`: result page number

**Returns**:

a list of the requested albums

**Return Type**:

`List[entities.Album]`

### search_track
```python
YaMusicClient.search_track(self, title, page=0)
```

Searches for the track with title `title`.

**Arguments**:

- `title`: track title
- `page`: result page number

**Returns**:

a list of the requested tracks

**Return Type**:

`List[entities.Track]`

### get_album
```python
YaMusicClient.get_album(self, album_id)
```

Returns the album with `album_id` id

**Arguments**:

- `album_id`: album id

**Returns**:

the requested album

**Return Type**:

`entities.Album`

### get_similar_tracks
```python
YaMusicClient.get_similar_tracks(self, track_id)
```

Returns tracks similar to the track with `track_id` id

**Arguments**:

- `track_id`: track id

**Returns**:

list of similar tracks

**Return Type**:

`List[entities.Track]`

## yamusic.exceptions

Exception classes for library-related errors.

### BaseError
```python
BaseError(*args, **kwargs)
```

Base module exception.

### AuthenticationError
```python
AuthenticationError(*args, **kwargs)
```

Authentication error.

### ResponseFormatError
```python
ResponseFormatError(*args, **kwargs)
```

Response formant is not correct.

### NotFoundError
```python
NotFoundError(*args, **kwargs)
```

Requested object not found.

## yamusic.schemas

Service entities serialization schemas.

### BaseSchema
```python
BaseSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Base serialization schema. All schemas should be inherited from it.

**Arguments**:

- `args`: positional arguments to be passed to `marshmallow.Schema`
- `envelope`: field that contains an object data
- `many_envelope`: field that contains a list of objects if `many` argument is `True`
- `kwargs`: named arguments to be passed to `marshmallow.Schema`

### GenreSchema
```python
GenreSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Genre entity serialization schema.

### UserSchema
```python
UserSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

User entity serialization schema.

### AlbumSchema
```python
AlbumSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Album entity serialization schema.

### ArtistSchema
```python
ArtistSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Artist entity serialization schema.

### TrackSchema
```python
TrackSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Track entity serialization schema.

### PlaylistSchema
```python
PlaylistSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Playlist entity serialization schema.

### SearchResultSchema
```python
SearchResultSchema(*args, envelope=None, many_envelope=None, **kwargs)
```

Search result entity serialization schema.

## yamusic.entities

Library types and entities.

### Visibility
```python
Visibility(*args, **kwargs)
```

Visibility type enumeration.

### Sex
```python
Sex(*args, **kwargs)
```

Sex type enumeration.

### SearchType
```python
SearchType(*args, **kwargs)
```

Search type enumeration.

### Genre
```python
Genre(id, title, fullTitle, tracksCount)
```

Music genre type.

### User
```python
User(uid, login, name, verified, sex)
```

User type.

### Album
```python
Album(id, title, year, trackCount, genre, releaseDate)
```

Album type.

### Artist
```python
Artist(id, name, composer, genres)
```

Artist type.

### Track
```python
Track(id, title, durationMs, albums, artists, available)
```

Audio track type.

### Playlist
```python
Playlist(kind, title, created, modified, trackCount, durationMs, visibility, owner, tracks, revision)
```

Music playlist type. Represents a collection of tracks plus some metainformaion.




# License

Unlicense
