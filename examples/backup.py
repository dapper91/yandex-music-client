"""
User playlists backup example.
"""

import csv
from yamusic.client import YaMusicClient


print("Connecting to Yandex Music...")

client = YaMusicClient('user', 'password')

with open('playlist-backup.csv', 'w', newline='') as backup_file:

    csv_writer = csv.DictWriter(backup_file, fieldnames=['playlist', 'artist', 'title', 'album'])
    csv_writer.writeheader()    

    print("Downloading user's playlists...")

    for playlist in client.get_playlists():

        print("Backing up '{}' playlist...".format(playlist.title))

        for track in client.get_playlist(playlist.kind):
            csv_writer.writerow({
                'playlist': playlist.title,
                'artist': track.artists[0].name,
                'title': track.title,
                'album': track.albums[0].title if track.albums else '',
            })
