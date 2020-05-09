
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
* [pydantic](https://pydantic-docs.helpmanual.io)


# Usage example

### Playlists backup
```python

import getpass
import csv
import sys

from yamusic import exceptions, YaMusicClient


username = getpass.getuser()
username = input(f"Login ({username}): ") or username
password = getpass.getpass("Password: ")

filename = 'backup.csv'
filename = input(f"filename: ({filename}): ") or filename

print("Connecting to Yandex Music...")

try:
    ym_client = YaMusicClient(username, password)
except exceptions.AuthenticationError:
    print("Authentication error: username or password is incorrect")
    sys.exit(1)


with open(filename, 'w', newline='') as backup_file:
    csv_writer = csv.DictWriter(backup_file, fieldnames=['playlist', 'artist', 'title', 'album'])
    csv_writer.writeheader()

    print("Downloading user's playlists...")

    for playlist in ym_client.get_playlists():
        print("Backing up '{}' playlist...".format(playlist.title))

        for track in ym_client.get_playlist(playlist.kind, rich_tracks=True):
            csv_writer.writerow({
                'playlist': playlist.title,
                'artist': track.artists[0].name,
                'title': track.title,
                'album': track.albums[0].title if track.albums else '',
            })


```

### Playlists manipulation
```python

from yamusic import YaMusicClient


client = YaMusicClient('user', 'password')

print("User's playlists:")
for playlist in client.get_playlists():
    print("{title} ({track_count})".format(
        title=playlist.title,
        track_count=playlist.track_count)
    )


playlist_name = 'Folk'
print("{} playlist:".format(playlist_name))

for track in client.get_playlist(title=playlist_name, rich_tracks=True).tracks:
    print("\t{title} - {artists} - {albums}".format(
        title=track.title,
        artists=', '.join(map(str, track.artists)),
        albums=', '.join(map(str, track.albums)))
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

https://dapper91.github.io/yandex-music-client/yamusic/api.html

# License

Unlicense
