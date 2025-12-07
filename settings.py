'''
Number of top tracks to fetch for each user.
'''
TOP_TRACK_NUM: int = 20

'''
Number of top artists to fetch for each user.
'''
TOP_ARTIST_NUM: int = 20

"""
Your S3 bucket name.
All Spotify-related cache, user lists, and playlist info
will be stored in this bucket.
"""
BUCKET_NAME: str = 'daiki-spotify'

"""
A list of user IDs:

{
  "users": ["<USER_ID_1>", "<USER_ID_2>"]
}

The user IDs listed here **must match** the environment variables  
set in the Lambda function (e.g., SPOTIFY_USER_1, SPOTIFY_USER_2).
"""
USERS_FILE_KEY: str = 'playlist_update_users.json'

"""
Initially an empty JSON object: {}

This file stores top_track and top artists tracks playlists uris
"""
PLAYLIST_INFO_FILE_KEY: str = 'playlists_info.json'
