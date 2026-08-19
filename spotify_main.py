from __future__ import annotations
import spotipy
from s3_spotify_cache_handler import S3SpotifyCacheHandler
from settings import *
import os
import logging
from spotipy.exceptions import SpotifyOauthError
from spotify_error import InvalidGrantError

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from s3_manager import S3Manager
    from json_manager import JsonManager
    from spotify_top_tracks import SpotifyTopTracks
    from spotify_top_artists_tracks import SpotifyTopArtistsTracks

# This file is part of the AWS Lambda Spotify automation system.
# It orchestrates the process of loading user info, refreshing Spotify tokens,
# generating top-track playlists, and saving results back to S3.

# Notice: To use this code, you must configure your environment variables
#         (CLIENT_ID, CLIENT_SECRET, and REDIRECT_URI).
#         The "user_id" does NOT need to be the user's Spotify account ID.
#         You may choose any unique identifier you prefer.
#         
#         In addition, the cache file, the users file, and the playlist info file
#         must be uploaded to your S3 bucket before running this Lambda.

logger = logging.getLogger(__name__)

class SpotifyMain:
    """
    Main controller class responsible for coordinating all Spotify operations
    within the AWS Lambda execution environment.
    
    Responsibilities:
    - Load user id and playlist info from S3
    - Initialize Spotify clients for each user
    - Handle token caching via S3
    - Execute top tracks and top artists playlist generation
    """
    def __init__(self, s3_manager: S3Manager, json_manager: JsonManager, spotify_top_tracks: SpotifyTopTracks, spotify_top_artists_tracks: SpotifyTopArtistsTracks):
        """
        Constructor for SpotifyMain.
        
        :param s3_manager: Handles loading/saving data to S3
        :param json_manager: Handles creation of JSON structures
        :param spotify_top_tracks: Logic for generating user top track playlists
        :param spotify_top_artists_tracks: Logic for generating top artist tracks playlists
        """
        self.scope = SCOPE
        self.s3_manager = s3_manager
        self.json_manager = json_manager
        self.spotify_top_tracks = spotify_top_tracks
        self.spotify_top_artists_tracks = spotify_top_artists_tracks
    
    def run(self):
        """
        Main execution function.
        
        Workflow:
        1. Load user info and playlist URIs from S3.
        2. For each registered user:
            - Check if the user is new. If the user is new, create json data.
            - Load Spotify API credentials from environment variables.
            - Load/refresh Spotify token via S3-based cache.
            - Run top tracks and top artists playlist creation.
            - Save playlist uris on s3.
        """
        # Load user id and playlist info from S3
        users_data = self.s3_manager.load_info(BUCKET_NAME, USERS_FILE_KEY)
        playlist_uri_data = self.s3_manager.load_info(BUCKET_NAME, PLAYLIST_INFO_FILE_KEY)

        if not users_data:
            logger.warning("No user data.")
            return

        for owner_id, owner_info in users_data.get('owners', {}).items():
            # Load user-specific Spotify credentials from environment variables stored in Lambda
            client_id = os.environ.get(f'E{owner_id}ClientId', None)
            client_secret = os.environ.get(f'E{owner_id}ClientSecret', None)
            redirect_url = os.environ.get(f'E{owner_id}RedirectUrl', None)

            # If any credentials are missing, skip the user
            if client_id is None or client_secret is None or redirect_url is None:
                logger.warning(f"Skipping {owner_id} because no client id or client secret was found.")
                continue
            users = owner_info.get('users', [])
            for user_info in users:
                user_id = user_info.get('id', None)
                if not user_id:
                    logger.warning(
                        "No user ID for owner_id=%s.",
                        owner_id
                    )
                    continue

                # Token cache stored in S3 instead of local filesystem
                cache_handler = S3SpotifyCacheHandler(
                                    s3_manager=self.s3_manager,
                                    bucket=BUCKET_NAME,
                                    key=f".cache-{user_id}"
                                )

                # Check if .cache file is on s3. If not, skip the user.
                cache_data = cache_handler.get_cached_token()
                if cache_data is None:
                    print(f"[WARN] No token cache for {user_id}. Please authenticate this user first.")
                    continue
                
                # Initialize authenticated Spotify client
                sp_auth = spotipy.oauth2.SpotifyOAuth(client_id=client_id,
                                                    client_secret=client_secret,
                                                    redirect_uri=redirect_url,
                                                    scope=self.scope,
                                                    cache_handler=cache_handler,
                                                    open_browser=False,
                                                    show_dialog=True)
                
                sp = spotipy.Spotify(auth_manager=sp_auth)

                # Log and check if the user is ready.
                try:
                    username = sp.me()['display_name']
                except SpotifyOauthError as e:
                    error_code = getattr(e, "error", None)
                    if error_code == "invalid_grant":
                        invalid_grant_error = InvalidGrantError(user_id)
                        logger.error(
                            "%s: %s",
                            type(invalid_grant_error).__name__,
                            invalid_grant_error
                        )
                        continue
                    raise

                print(f"user_id: {user_id}, username: {username} is now logged in.")

                # check if the user is new
                if self.json_manager.is_new_user(playlist_uri_data, user_id):
                    # if new, make playlist uri data
                    playlist_uri_data = self.json_manager.make_new_user(playlist_uri_data, user_id)

                # Generate playlists for this user
                self.spotify_top_tracks.main(sp, user_id, playlist_uri_data)
                self.spotify_top_artists_tracks.main(sp, user_id, playlist_uri_data)

                # Save updated playlist URIs back to S3
                self.s3_manager.save_info(BUCKET_NAME, PLAYLIST_INFO_FILE_KEY, playlist_uri_data)