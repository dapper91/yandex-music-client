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

### Constructor

Creates a client instance and authenticates on the service:

```python

client = YaMusicClient('dima', 'password123')

```

Constructor arguments:

- `login` - yandex account user name
- `password` - yandex account password

## License

Unlicense
