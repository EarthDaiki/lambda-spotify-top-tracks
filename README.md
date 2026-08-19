# Spotify Top Playlists on AWS Lambda

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=awslambda&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon-S3-green?logo=amazons3&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-Web_API-1DB954?logo=spotify&logoColor=white)

A Python application that retrieves a user's top tracks and top artists from the Spotify Web API, then automatically creates and updates private playlists for different time ranges. The regular workflow runs on AWS Lambda and stores the user registry, playlist URIs, and OAuth tokens in Amazon S3. The same workflow can also be run locally.

## Features

- Creates and updates top-track playlists for `short_term`, `medium_term`, and `long_term`
- Creates and updates playlists containing popular tracks from the user's top artists for the same three time ranges
- Compares the existing track order with the latest results and replaces tracks only when something changed
- Persists playlist URIs and Spotify OAuth tokens in S3
- Supports multiple Spotify users under one configuration owner (`owner_id`)
- Logs and skips a user when its refresh token has expired or been revoked, then continues processing the remaining users
- Runs the Lambda workflow locally through `local_run.py`

By default, the application retrieves 20 top tracks and 20 top artists for each time range. These limits are configured with `TOP_TRACK_NUM` and `TOP_ARTIST_NUM` in `settings.py`.

## Terminology

This project distinguishes between an `owner_id` and an actual Spotify user ID.

- `owner_id`: An arbitrary configuration identifier used to select a Spotify application's Client ID, Client Secret, and Redirect URI
- Spotify user ID: The actual Spotify account ID returned by `sp.me()["id"]` after OAuth authentication

Environment variables are associated with an `owner_id`, while S3 token caches and playlist metadata are associated with an actual Spotify user ID.

## Requirements

- Python 3.10 or later
- An application created in the Spotify Developer Dashboard
- An Amazon S3 bucket
- Local AWS credentials or a Lambda execution role with access to the bucket
- Python dependencies:
  - `boto3>=1.42.4`
  - `spotipy>=2.25.1`

Install the dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Environment Variables

### Shared configuration

| Name | Required | Description |
|---|---:|---|
| `BucketName` | Yes | S3 bucket that stores the JSON files and OAuth token caches |

### Spotify configuration for each owner

Replace `OWNER_ID` with your chosen `owner_id` and define the following variables:

| Name | Description |
|---|---|
| `E<OWNER_ID>ClientId` | Spotify application Client ID |
| `E<OWNER_ID>ClientSecret` | Spotify application Client Secret |
| `E<OWNER_ID>RedirectUrl` | Redirect URI registered for the Spotify application |

For example, when the `owner_id` is `myapp`:

```powershell
$env:BucketName = "your-s3-bucket"
$env:EmyappClientId = "your-client-id"
$env:EmyappClientSecret = "your-client-secret"
$env:EmyappRedirectUrl = "http://127.0.0.1:8888/callback"
```

The Redirect URI must exactly match a URI registered in the Spotify Developer Dashboard. Do not commit secret values to the repository.

When running locally, boto3 uses its standard AWS credential provider chain. For example, to use a named AWS profile:

```powershell
$env:AWS_PROFILE = "spotify-local"
$env:AWS_DEFAULT_REGION = "us-west-2"
```

## Data Stored in S3

The object keys below are configured in `settings.py`.

### `playlist_update_users.json`

Stores the relationship between configuration owners and the actual Spotify users authenticated through each owner's Spotify application.

```json
{
  "owners": {
    "OWNER_ID": {
      "users": [
        { "id": "SPOTIFY_USER_ID_1" },
        { "id": "SPOTIFY_USER_ID_2" }
      ]
    }
  }
}
```

The file may initially contain an empty object:

```json
{}
```

When `spotify_auth.py` registers a Spotify user, it first removes that user from every other owner and then assigns it to the selected owner.

### `playlists_info.json`

Stores the six managed playlist URIs for each Spotify user. Create this object in S3 with an empty JSON object before the first playlist update:

```json
{}
```

After processing a user, it has the following structure:

```json
{
  "SPOTIFY_USER_ID": {
    "current_user_top_tracks_uris": {
      "short_term": "spotify:playlist:...",
      "medium_term": "spotify:playlist:...",
      "long_term": "spotify:playlist:..."
    },
    "artist_top_tracks_uris": {
      "short_term": "spotify:playlist:...",
      "medium_term": "spotify:playlist:...",
      "long_term": "spotify:playlist:..."
    }
  }
}
```

### `.cache-<SPOTIFY_USER_ID>`

Stores Spotipy's access token, refresh token, expiration information, scopes, and related OAuth data as JSON.

```text
s3://<BucketName>/.cache-<SPOTIFY_USER_ID>
```

These objects contain credentials and must not be made public.

## Initial Authentication and Reauthentication

AWS Lambda does not provide an interactive browser, so OAuth authentication must be completed on a local computer. `spotify_auth.py` temporarily keeps the token in a `MemoryCacheHandler`, retrieves the actual Spotify user ID after authentication, and then saves the token to S3.

1. Set the target `owner_id` near the bottom of `spotify_auth.py`:

   ```python
   owner_id = "myapp"
   ```

2. Set `BucketName`, the Spotify environment variables for that owner, and local AWS credentials.
3. Confirm that the Redirect URI is registered in the Spotify Developer Dashboard.
4. Run:

   ```powershell
   python spotify_auth.py
   ```

5. Sign in to the intended Spotify account in the browser and approve access.

After successful authentication, the script:

- Writes `.cache-<SPOTIFY_USER_ID>` to S3
- Registers the owner-to-user relationship in `playlist_update_users.json`
- Prints the authenticated display name and owner

The script uses `check_cache=False`, so every execution starts a new authorization flow instead of reusing an existing token cache.

## Running Locally

`local_run.py` calls `lambda_handler({}, None)` and runs the same workflow used by Lambda.

```powershell
python local_run.py
```

Before running it, define the environment variables for every owner registered in S3. An owner without complete Spotify credentials is logged and skipped.

This is not a read-only connectivity test. It can create and modify Spotify playlists and writes the updated `playlists_info.json` back to S3.

Example successful response:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Success\"}"
}
```

## Deploying to AWS Lambda

1. Create a Lambda function using Python 3.10 or later.
2. Set the handler to:

   ```text
   lambda_function.lambda_handler
   ```

3. Deploy the project's Python source files.
4. Include `spotipy` and its dependencies in the deployment package or attach them as a Lambda Layer.
5. Configure `BucketName` and the three Spotify environment variables for each owner.
6. Grant the Lambda execution role `s3:GetObject` and `s3:PutObject` for the required objects.
7. Confirm that `playlist_update_users.json`, `playlists_info.json`, and the registered users' token caches exist in S3 before invoking the function.

The local `lambda_layer/python/` directory contains a prepared copy of Spotipy and related packages. `lambda_layer/` is excluded by `.gitignore`. When publishing a Layer, use dependencies compatible with the Lambda Python runtime and execution environment.

## Expired or Revoked Tokens

When Spotify returns `invalid_grant` for a refresh token, `spotify_main.py` logs an `InvalidGrantError` and skips only that Spotify user. Processing continues for the remaining users. If no unhandled exception occurs, the overall Lambda invocation still returns `200 Success`.

Example log entry:

```text
[ERROR] spotify_main: InvalidGrantError: User 'SPOTIFY_USER_ID' must reauthenticate with Spotify. Run spotify_auth.py with an owner id
```

Set the appropriate owner in `spotify_auth.py` and reauthenticate locally. Authenticating the same Spotify user replaces its S3 token cache.

Unhandled errors other than `invalid_grant` are caught by `lambda_function.py`, which returns a `500` response containing the error and traceback.

## Spotify Scopes

The application currently requests these scopes:

```text
user-read-recently-played
user-read-playback-state
user-top-read
user-read-private
user-library-read
playlist-modify-private
playlist-read-private
user-modify-playback-state
```

Managed playlists are created as private playlists with `public=False`.

## Project Structure

| File | Purpose |
|---|---|
| `lambda_function.py` | AWS Lambda entry point, dependency assembly, and response handling |
| `local_run.py` | Local entry point that invokes the Lambda handler |
| `spotify_auth.py` | Browser OAuth, actual Spotify user discovery, S3 token storage, and user registration |
| `spotify_main.py` | Main orchestrator that processes owners and Spotify users |
| `spotify_top_tracks.py` | Creates and updates top-track playlists for each time range |
| `spotify_top_artists_tracks.py` | Creates and updates top-artist-track playlists for each time range |
| `playlist_manager.py` | Creates playlists and retrieves, removes, adds, or updates playlist content |
| `json_manager.py` | Initializes the playlist URI structure for a new user |
| `s3_manager.py` | Reads and writes JSON objects in S3 |
| `s3_spotify_cache_handler.py` | Connects Spotipy's cache interface to S3 |
| `spotify_error.py` | Defines the custom error used for an invalid refresh token |
| `settings.py` | Configures S3 object keys, result limits, and Spotify scopes |
| `requirements.txt` | Lists direct Python dependencies |
| `.gitignore` | Excludes caches, editor settings, and the local Lambda Layer directory |

## Notes and Limitations

- If `playlist_update_users.json` is empty or missing, the Lambda workflow exits without processing a user.
- Create `playlists_info.json` in S3 with `{}` before the first playlist update.
- Playlist-list and playlist-item retrieval do not implement pagination. Accounts with many playlists or playlists with many tracks may only process the first page.
- `spotify_auth.py` assigns a given Spotify user to only one owner at a time.
- Lambda logs are sent to CloudWatch Logs. Local logs are written to standard output or standard error.
- A `200` response does not guarantee that every user was processed. Users with missing owner credentials, missing token caches, or `invalid_grant` errors are skipped, so review the logs as well.
