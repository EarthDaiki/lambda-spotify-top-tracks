from typing import List, Dict, Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from spotipy import Spotify

class PlaylistManager:
    """
    Manages playlist creation, updates, and metadata changes.
    """
    def __init__(self):
        """
        Even though the constructor does not currently perform initialization,
        it is included for consistency and future scalability.
        """
        pass

    def record_cuttu_playlist_uri(self, data: Dict[str, Any], playlist_uri: str, term: str, user_id: str) -> Dict[str, Any]:
        """
        Update the stored playlist URI for the user's top tracks.
        This modifies the value of playlist info json that is stored in S3.

        Args:
            data: The full playlist info dictionary loaded from S3.
            playlist_uri: The new playlist URI to store.
            term: The Spotify time range (e.g., 'short_term', 'medium_term', 'long_term').
            user_id: The user identifier used in the S3 JSON.

        Returns:
            Updated dictionary containing the new playlist URI.
        """
        data[user_id]["current_user_top_tracks_uris"][term] = playlist_uri
        return data
    
    def record_attu_playlist_uri(self, data: Dict[str, Any], playlist_uri: str, term: str, user_id: str) -> Dict[str, Any]:
        """
        Update the stored playlist URI for the user's artist top tracks.
        This modifies the value of playlist info json that is stored in S3.

        Returns:
            Updated dictionary containing the new playlist URI.
        """
        data[user_id]["artist_top_tracks_uris"][term] = playlist_uri
        return data

    def get_songs_uri(self, sp: Spotify, playlist_uri: str) -> List[str]:
        """
        Retrieve all track URIs currently inside the given playlist.

        Args:
            sp: The authenticated Spotify client.
            playlist_uri: The playlist's URI.

        Returns:
            A list of track URIs inside the playlist.
        """
        prev_track_uris = []
        songs = sp.playlist_items(playlist_id=playlist_uri)
        for song in songs['items']:
            uri = song['track']['uri']
            prev_track_uris.append(uri)
        return prev_track_uris

    def get_my_playlists(self, sp: Spotify) -> Dict[str, Any]:
        """
        Get all playlists owned by the user.

        Args:
            sp: The authenticated Spotify client.

        Returns:
            A dictionary of user playlists data returned by the Spotify API.
        """
        results = sp.current_user_playlists()
        return results

    def make_playlist(self, sp: Spotify, name: str, public=False, collaborative=False, description: Optional[str]=None) -> Dict[str, Any]:
        """
        Create a new playlist for the user.

        Args:
            sp: The authenticated Spotify client.
            name: Name of the new playlist.
            public: Whether the playlist is public.
            collaborative: Whether the playlist is collaborative.
            description: Playlist description text.

        Returns:
            The created playlist object.
        """
        new_playlist = sp.user_playlist_create(user=sp.me()['id'], name=name, public=public, collaborative=collaborative, description=description)
        return new_playlist

    def delete_all_songs(self, sp: Spotify, playlist_uri: str, prev_track_uris: List[str]):
        """
        Remove all tracks from a playlist before updating it.

        Args:
            sp: The authenticated Spotify client.
            playlist_uri: URI of the playlist to clear.
            prev_track_uris: List of URIs to remove.
        """
        if prev_track_uris:
            sp.playlist_remove_all_occurrences_of_items(playlist_id=playlist_uri, items=prev_track_uris)

    def add_to_playlist(self, sp: Spotify, track_uris: List[str], playlist_uri: str):
        """
        Add a list of tracks to a playlist.

        Args:
            sp: The authenticated Spotify client.
            track_uris: Track URIs to add.
            playlist_uri: Playlist to append tracks to.
        """
        sp.playlist_add_items(playlist_id=playlist_uri, items=track_uris)

    def change_playlist_details(self, sp: Spotify, playlist_uri: str, name=None, public=None, collaborative=None, description: Optional[str]=None):
        """
        Update playlist metadata (name, public settings, description).

        Args:
            sp: The authenticated Spotify client.
            playlist_uri: Playlist to update.
            name: New playlist name (optional).
            public: Change public visibility (optional).
            collaborative: Change collaborative setting (optional).
            description: Change playlist description (optional).
        """
        sp.playlist_change_details(playlist_id=playlist_uri, name=name, public=public, collaborative=collaborative, description=description)