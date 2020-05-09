"""
User's playlists backup example.
"""

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
