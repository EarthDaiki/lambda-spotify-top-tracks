# ![Spotify Badge](https://img.shields.io/badge/Spotify-Lambda-green?logo=spotify&logoColor=white) Lambda Spotify Top Tracks

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazonaws&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS-S3-yellow?logo=amazonaws&logoColor=white)

## Overview
This project automatically manages Spotify playlists based on your top tracks and top artists.  
Built for **AWS Lambda**, it interacts with Spotify's API and stores playlist metadata in Amazon S3.  

## Requirements
- Python 3.10+
- `spotipy` library
- `boto3` for AWS S3 integration
- AWS Lambda with environment variables for Spotify credentials
- S3 bucket containing:
  - `playlist_update_users.json`(default): list of user IDs
  - `playlists_info.json`(default): initially empty, will store playlist URIs
  - `.cache-USER_ID`: Spotify cache file for each user

## Environment Variables
Each user must have the following variables set in Lambda or your environment:

- `E<USER_ID>ClientId`
- `E<USER_ID>ClientSecret`
- `E<USER_ID>RedirectUrl`

**Note:** The `user_id` does **not** need to match your Spotify account ID. You can choose any unique string, though it is recommended to keep it consistent.

## Usage
```bash
# Deploy to AWS Lambda
# 1. Upload the code to a Lambda function.
# 2. Set the required environment variables (client ID, client secret, redirect URL) for each user.
# 3. Set BUCKET_NAME in settings.py. If you make your own key, change the FILE_KEY name.
# 4. Ensure the following S3 files exist:
#    - users json file (default -> playlist_update_users.json)
#    - playlists info file (default -> playlists_info.json)
#    - .cache-USER_ID files for each Spotify user.
# 5. Invoke the Lambda function. It will update playlists for all users listed in playlist_update_users.json.
```

## Lambda Function Behavior

The Lambda function will:

- Load user info and playlist info JSON from S3
- Authenticate Spotify users using cached tokens
- Create or update playlists for top tracks and top artists
- Upload updated playlist info back to S3

## S3 File Structure

**playlist_update_users.json**(default):

```json
{
  "users": ["USER_ID_1", "USER_ID_2"]
}
```

**playlists_info.json (initially empty)**(default):

```json
{
  "USER_ID_1": {},
  "USER_ID_2": {}
}
```

**Spotify Cache Files (`.cache-USER_ID`)**:

- Each Spotify user has a cache file stored in S3 with the naming convention `.cache-USER_ID`.
- These cache files store OAuth access tokens and refresh tokens used for authentication.
- Example S3 path: `s3://YOUR_BUCKET_NAME/.cache-USER_ID`
- Required for the AWS Lambda function to authenticate Spotify users without manual login each time.
- If a cache file does not exist or is invalid, the user must authenticate manually via Spotify OAuth outside of Lambda.

## Modules

| File | Description |
|------|-------------|
| `lambda_handler.py` | Main Lambda entry point |
| `spotify_main.py` | Orchestrates playlist updates |
| `spotify_top_tracks.py` | Fetch top tracks and update playlists |
| `spotify_top_artists_tracks.py` | Fetch top artists tracks and update playlists |
| `s3_manager.py` | Handles S3 read/write operations |
| `json_manager.py` | Manages user playlist JSON structures |
| `s3_spotify_cache_handler.py` | Manages Spotify token caching in S3 |

## Notes

- Designed for professionals who want automated playlist management with multiple Spotify users.
- Ensure all environment variables and S3 files are correctly set before running.
- Supports short, medium, and long-term Spotify time ranges.