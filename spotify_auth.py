import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler

from s3_manager import S3Manager
from s3_spotify_cache_handler import S3SpotifyCacheHandler
from settings import BUCKET_NAME, SCOPE, USERS_FILE_KEY

class Auth:
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.s3_manager = S3Manager()
        self.scope = SCOPE

    def get_required_environment(self, name: str):
        value = os.getenv(name, None)
        if not value:
            raise RuntimeError(
                f"Required environment variable is missing: {name}"
            )
        return value

    def authenticate(self) -> tuple[spotipy.Spotify, dict]:
        client_id = self.get_required_environment(
            f"E{self.owner_id}ClientId"
        )
        client_secret = self.get_required_environment(
            f"E{self.owner_id}ClientSecret"
        )
        redirect_url = self.get_required_environment(
            f"E{self.owner_id}RedirectUrl"
        )

        memory_cache_handler = MemoryCacheHandler()
        oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_url,
            scope=self.scope,
            cache_handler=memory_cache_handler,
            open_browser=True,
            show_dialog=True
        )

        oauth.get_access_token(
            as_dict=False,
            check_cache=False,
        )

        token_info = memory_cache_handler.get_cached_token()
        if not token_info:
            raise RuntimeError("Spotify token was not created.")
        return spotipy.Spotify(auth_manager=oauth), token_info

    def load_users_info_file(self):
        return self.s3_manager.load_info(BUCKET_NAME, USERS_FILE_KEY)
    def save_user_info(self, data: dict | None, user_id: str):
        data = data or {}
        owners = data.setdefault("owners", {})

        for owner_data in owners.values():
            users = owner_data.get("users", [])

            owner_data["users"] = [
                user
                for user in users
                if user.get("id") != user_id
            ]

        users = (
            owners
            .setdefault(self.owner_id, {})
            .setdefault("users", [])
        )

        users.append({"id": user_id})
        self.s3_manager.save_info(BUCKET_NAME, USERS_FILE_KEY, data)

    def save_user_cache(self, user_id, token_info):
        s3_cache_handler = S3SpotifyCacheHandler(
            self.s3_manager,
            BUCKET_NAME,
            f".cache-{user_id}"
        )
        s3_cache_handler.save_token_to_cache(
            token_info
        )

if __name__ == "__main__":
    owner_id = "22cunbuveglybbsdtu6djzu4a"
    auth = Auth(owner_id)
    sp, token_info = auth.authenticate()
    profile = sp.me()
    user_id = profile["id"]
    display_name = profile["display_name"]
    data = auth.load_users_info_file()
    auth.save_user_cache(user_id, token_info)
    auth.save_user_info(data, user_id)
    print(f"Hello {display_name}")
    print(f"{display_name} under owner {owner_id}")
    print("You were registed successfully.")