from datetime import date
from settings import *
from typing import Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
    from playlist_manager import PlaylistManager
    from spotipy import Spotify

class SpotifyTopArtistsTracks:
    """
    This class handles the retrieval and updating of Spotify playlists
    containing the top tracks from a user's top artists. 
    """
    def __init__(self, playlist_manager: PlaylistManager):
        """
        Initialize the SpotifyTopArtistsTracks instance.

        Parameters:
            playlist_manager (PlaylistManager): A helper class for Spotify playlist operations.
        """
        self.playlist_manager = playlist_manager

    def get_top_artists(self, sp: Spotify, term: str) -> Dict:
        """
        Retrieve a user's top artists from Spotify.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            term (str): Time range for top artists ('short_term', 'medium_term', 'long_term').

        Returns:
            dict: Spotify API response containing top artists.
        """
        return sp.current_user_top_artists(limit=TOP_ARTIST_NUM, offset=0, time_range=term)
    
    def get_top_artists_tracks(self, sp: Spotify, artist_id: str) -> Dict:
        """
        Retrieve the top tracks for a specific artist.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            artist_id (str): Spotify artist ID.

        Returns:
            dict: Spotify API response containing the artist's top tracks.
        """
        return sp.artist_top_tracks(artist_id)
    
    def update_playlist(self, sp: Spotify, playlist_uri: str, term: str, prev_track_uris: List[str]) -> bool:
        """
        Update a playlist with top tracks from top artists.
        Compares with previous tracks and only updates if changed.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            playlist_uri (str): Playlist URI to update.
            term (str): Time range for top artists.
            prev_track_uris (List[str]): Previously stored track URIs.

        Returns:
            bool: True if playlist was modified, False if no changes.
        """
        artists = self.get_top_artists(sp, term)
        playlist_tracks = []
        for artist in artists['items']:
            tracks = self.get_top_artists_tracks(sp, artist['id'])
            for track in tracks['tracks']:
                playlist_tracks.append(track['uri'])
        if prev_track_uris == playlist_tracks:
            return False
        else:
            for i in range(0, len(prev_track_uris), 100):
                self.playlist_manager.delete_all_songs(sp, playlist_uri, prev_track_uris[i:i+100])
            for i in range(0, len(playlist_tracks), 100):
                self.playlist_manager.add_to_playlist(sp, playlist_tracks[i:i+100], playlist_uri)
            return True

    def main(self, sp: Spotify, user_id: str, playlist_uri_data: Dict[str, Dict]):
        """
        Main function to manage all top artists playlists for a user.
        Creates new playlists or updates existing ones.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            username (str): User ID.
            playlist_uri_data (dict): Dictionary storing playlist URIs.
        """
        today = date.today()
        my_playlists = self.playlist_manager.get_my_playlists(sp)

        for term, recorded_playlist_uri in list(playlist_uri_data[user_id]["artist_top_tracks_uris"].items()):
            print(f"=====top artists {term}=====")
            for my_playlist in my_playlists['items']:
                if recorded_playlist_uri == my_playlist['uri']:
                    print('playlist exists.')
                    self.playlist_manager.change_playlist_details(sp, my_playlist['uri'], description=f'my {term} playlist on {today}')
                    print("details are changed.")
                    break
            else:
                my_playlist = self.playlist_manager.make_playlist(sp, name=f'{term} top artists tracks', description=f'my {term} playlist on {today}')
                playlist_uri_data = self.playlist_manager.record_attu_playlist_uri(playlist_uri_data, my_playlist['uri'], term, user_id)
                print("playlist is made.")

            prev_track_uris = self.playlist_manager.get_songs_uri(sp, my_playlist['uri'])
            if self.update_playlist(sp, my_playlist['uri'], term, prev_track_uris):
                print("modified")
            else:
                print("NOT modified")