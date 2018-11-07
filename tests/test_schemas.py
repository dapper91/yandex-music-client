import os
import unittest

from yamusic.schemas import *
from . import THIS_DIR

class TestGenreSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(THIS_DIR, "./data/genres.json")) as file:
            cls.genres_data = file.read()

    def test_genres_deserialization(self):
        genres = GenreSchema(many_envelope='result', many=True).loads(self.genres_data).data
        
        self.assertEqual(len(genres), 27)

        titles = [genre.title for genre in genres]
        expected_titles = [
            "Музыка всех жанров","Поп","Инди","Рок","Метал","Альтернатива","Электроника","Танцевальная",
            "Рэп и хип-хоп","R&B","Джаз","Блюз","Регги","Ска","Панк","Музыка мира","Классика","Эстрада","Другое",
            "Шансон","Кантри","Саундтреки","Лёгкая музыка","Авторская песня","Детская","Аудиосказки","Советская музыка"
        ]
        
        self.assertCountEqual(titles, expected_titles)

        self.assertEqual(3948118, [genre.tracksCount for genre in genres if genre.title == 'Рок'][0])


class TestPlaylistsSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(THIS_DIR, "./data/playlists.json")) as file:
            cls.playlists_data = file.read()

    def test_playlists_deserialization(self):
        playlists = PlaylistSchema(many_envelope='result', many=True).loads(self.playlists_data).data

        self.assertEqual(len(playlists), 24)
        self.assertTrue(all([playlist.tracks is None for playlist in playlists]))



class TestPlaylistSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(THIS_DIR, "./data/playlist.json")) as file:
            cls.playlist_data = file.read()

    def test_playlist_deserialization(self):
        playlists = PlaylistSchema(many_envelope='result', many=True).loads(self.playlist_data).data

        self.assertEqual(len(playlists), 1)

        playlist = playlists[0]
        
        self.assertEqual(playlist.kind, 1084)
        self.assertEqual(len(playlist.tracks), 11)
        self.assertEqual(playlist.title, "Funk")

        track_titles = [track.title for track in playlist]

        expected_track_titles = [
            "Snow (Hey Oh)","Californication","Dani California","Can't Stop","Dark Necessities",
            "Otherside","Scar Tissue","Stadium Arcadium","Under The Bridge","Make You Feel Better","Two Princes"
        ]

        self.assertCountEqual(track_titles, expected_track_titles)

        track = [track for track in playlist.tracks if track.title == 'Snow (Hey Oh)'][0]
        
        self.assertEqual(len(track.artists), 1)
        self.assertEqual(track.artists[0].name, "Red Hot Chili Peppers")
        
        self.assertEqual(len(track.albums), 1)
        self.assertEqual(track.albums[0].title, "The Studio Album Collection 1991-2011")
        self.assertEqual(track.albums[0].year, 2014)


class TestPlaylistSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(THIS_DIR, "./data/search_result.json")) as file:
            cls.search_result_data = file.read()

        with open(os.path.join(THIS_DIR, "./data/search_result_tracks.json")) as file:
            cls.search_result_tracks_data = file.read()

    def test_search_result_deserialization(self):
        search_reuslt = SearchResultSchema(many_envelope='result').loads(self.search_result_data).data

        self.assertEqual(len(search_reuslt.albums), 10)
        self.assertEqual(len(search_reuslt.artists), 6)
        self.assertEqual(len(search_reuslt.tracks), 20)
        self.assertEqual(len(search_reuslt.playlists), 4)

    def test_search_result_tracks_deserialization(self):
        search_reuslt_tracks = SearchResultSchema(many_envelope='result').loads(self.search_result_tracks_data).data.tracks
        self.assertEqual(len(search_reuslt_tracks), 20)

        titles = [track.title for track in search_reuslt_tracks]
        expected_titles = [
            "Clocks","Clocks (Radio Edit)","Clocks/Relojes (feat. Coldplay & Lele)","Clocks","Clocks [Coldplay Cover]",
            "Clocks (Made Famous by Coldplay)","Clocks","Clocks [Coldplay Cover]","Clocks","Clocks [Coldplay Cover]",
            "Clocks [Coldplay Cover]","Clocks [In the Style of Coldplay]","Clocks [In the Style of Coldplay] {Karaoke Version}",
            "Clocks (made famous by Coldplay)","Clocks [In the Style of Coldplay] {Karaoke Lead Vocal Version}",
            "Clocks [Made Famous by Coldplay]","Animals","Clocks (made famous by Coldplay)","Clocks [Made Famous by Coldplay]","Clocks [Coldplay Cover]"
        ]

        self.assertCountEqual(titles, expected_titles)