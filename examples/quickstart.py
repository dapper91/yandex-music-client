"""
Quick start example.
"""

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
