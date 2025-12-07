import json
import traceback
from playlist_manager import PlaylistManager
from s3_manager import S3Manager
from json_manager import JsonManager
from spotify_top_tracks import SpotifyTopTracks
from spotify_top_artists_tracks import SpotifyTopArtistsTracks
from spotify_main import SpotifyMain

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    This function initializes all managers and orchestrates the Spotify playlist update workflow.
    It loads required managers, constructs the SpotifyMain controller,
    and triggers the processing of user playlists stored in S3.
    """
    try:
        # Initialize managers responsible for playlist handling, S3 interactions, and JSON operations.
        playlist_manager = PlaylistManager()
        s3_manager = S3Manager()
        json_manager = JsonManager()
        spotify_top_tracks = SpotifyTopTracks(playlist_manager)
        spotify_top_artists_tracks = SpotifyTopArtistsTracks(playlist_manager)

        # Main orchestrator responsible for running all Spotify-related logic.
        spotify_main = SpotifyMain(
            s3_manager,
            json_manager,
            spotify_top_tracks,
            spotify_top_artists_tracks
        )

        # Execute the core Spotify update process.
        spotify_main.run()

        # If no exceptions occur, return a successful API response.
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Success"})
        }
        
    except Exception as e:
        # Capture full traceback for debugging within CloudWatch logs.
        tb = traceback.format_exc()
        print(tb)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "traceback": tb
            })
        }