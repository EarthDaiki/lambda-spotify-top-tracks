from datetime import date
from settings import *
from typing import Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
    from playlist_manager import PlaylistManager
    from spotipy import Spotify

class SpotifyTopTracks:
    """
    Handles creating and updating Spotify playlists with a user's top tracks.
    """
    def __init__(self, playlist_manager: PlaylistManager):
        """
        Initialize with PlaylistManager instance.

        Parameters:
            playlist_manager (PlaylistManager): Helper class for playlist operations.
        """
        self.playlist_manager = playlist_manager
        
    
    def update_playlist(self, sp: Spotify, term: str, prev_track_uris: List[str], playlist_uri: str) -> bool:
        """
        Update a playlist with the user's top tracks.
        If the playlist is unchanged from the previous version, nothing is done.
        Otherwise, all songs in the playlist are deleted and new tracks are added.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            term (str): Time range for top tracks ('short_term', 'medium_term', 'long_term').
            prev_track_uris (List[str]): Previously stored track URIs in the playlist.
            playlist_uri (str): Playlist URI to update.

        Returns:
            bool: True if the playlist was modified, False if no changes.
        """
        track_uris = []
        results = sp.current_user_top_tracks(limit=TOP_TRACK_NUM, offset=0, time_range=term)
        for number, result in enumerate(results['items']):
            uri = result['uri']
            track_uris.append(uri)
        if prev_track_uris == track_uris:
            return False
        else:
            self.playlist_manager.delete_all_songs(sp, playlist_uri, prev_track_uris)
            self.playlist_manager.add_to_playlist(sp, track_uris, playlist_uri)
            return True
    
    def main(self, sp: Spotify, user_id: str, playlist_uri_data: Dict[str, Dict]):
        """
        Main function to manage all top tracks playlists for a user.
        Creates new playlists or updates existing ones.

        Parameters:
            sp (Spotify): Authenticated Spotipy client.
            username (str): User ID.
            playlist_uri_data (dict): Dictionary storing playlist URIs per user.
        """
        today = date.today()
        my_playlists = self.playlist_manager.get_my_playlists(sp)

        for term, recorded_playlist_uri in list(playlist_uri_data[user_id]["current_user_top_tracks_uris"].items()):
            print(f"=====top song {term}=====")
            for my_playlist in my_playlists['items']:
                # if recored playlist uri's playlist does not exist, create a new playlist.
                if recorded_playlist_uri == my_playlist['uri']:
                    print('playlist exists.')
                    self.playlist_manager.change_playlist_details(sp, my_playlist['uri'], description=f'my {term} playlist on {today}')
                    print("details are changed.")
                    break
            else:
                my_playlist = self.playlist_manager.make_playlist(sp, name=f'{term} top tracks', description=f'my {term} playlist on {today}')
                playlist_uri_data = self.playlist_manager.record_cuttu_playlist_uri(playlist_uri_data, my_playlist['uri'], term, user_id)
                print("playlist is made.")

            prev_track_uris = self.playlist_manager.get_songs_uri(sp, my_playlist['uri'])
            if self.update_playlist(sp, term, prev_track_uris, my_playlist['uri']):
                print("modified")
            else:
                print("NOT modified.")
            