# Yandex Music client

A python3 Yandex Music (https://music.yandex.ru) Client Library.

This library doesn't provide an ability to download or listen audio tracks bypassing the
official audio players, which violates the user agreements (https://yandex.ru/legal/music_termsofuse/). 
The purpose of the library is to provide a way to backup your playlists, import/export your playlists 
from/to your local audio library or other music services like Spotify, Apple Music and so on.

**NB**: This module uses an unofficial Yandex Music service api that has been grasped through some 
reverse engineering research which means it can be modified any time and the client would break down.

## Dependencies

* requests (http://docs.python-requests.org)



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

for track in client.get_playlist(playlist_name).tracks:
    print("\t{title} - {authors} ({albums})".format(
        title=track.title, 
        authors=', '.join(track.authors), 
        albums=', '.join(track.albums))
    )



playlist = client.create_playlist('Russian Rock')

for artist_name, track_name in [
        ('ДДТ',  'В последнюю осень'), 
        ('Ария', 'Я здесь'), 
        ('Кино', 'Хочу перемен'), 
        ('ДДТ',  'Просвистела')
    ]:

    track = client.search_track('{} - {}'.format(track_name, artist_name))

    client.add_tracks_to_playlist(playlist, [track], prevent_dublicates=True)


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
- `logger` - a python logger to use to instead of a default logger (default: None)
- `remember_me` - force the service to remember the identity of the user between sessions (default: True)

## License

MIT
