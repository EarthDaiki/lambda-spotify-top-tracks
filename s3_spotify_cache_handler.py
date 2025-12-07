from spotipy.cache_handler import CacheHandler
from typing import Optional, Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from s3_manager import S3Manager

class S3SpotifyCacheHandler(CacheHandler):
    """
    A Spotify cache handler that stores and retrieves OAuth tokens from Amazon S3.

    This class integrates Spotipy's cache system with AWS S3 storage, allowing
    tokens to persist across AWS Lambda executions—even though Lambda has no
    persistent local file system.

    Attributes:
        s3_manager (S3Manager): Custom S3 manager used for loading and saving JSON.
        bucket (str): Name of the S3 bucket where cache is stored.
        key (str): S3 object key used as the cache filename.
        cache_data (dict | None): Cached token information retrieved from S3.
    """
    def __init__(self, s3_manager: S3Manager, bucket: str, key: str):
        """
        Initialize the S3-based Spotify cache handler.

        Parameters:
            s3_manager (S3Manager): Helper class for S3 read/write operations.
            bucket (str): Target S3 bucket name.
            key (str): S3 object key representing this user's cache file.
        """
        self.s3_manager = s3_manager
        self.bucket = bucket
        self.key = key
        self.cache_data = self._load_from_s3()

    def _load_from_s3(self) -> Optional[Dict[str, Any]]:
        """
        Load token data from S3.

        Returns:
            dict | None: Token data if found, otherwise None.

        Notes:
            This method is called during initialization to populate
            `self.cache_data`. If no cache exists, S3Manager returns `{}`,
            which this method treats as valid empty data.
        """
        cache_data = self.s3_manager.load_info(self.bucket, self.key)
        return cache_data

    def get_cached_token(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the cached Spotify OAuth token.

        Returns:
            dict | None: The token information, or None if no cache exists.

        Notes:
            Spotipy calls this method automatically when performing
            authorization in SpotifyOAuth. Besides, this fuction will be
            called manually to check if cache is on s3 before SpotifyOAuth.
        """
        if self.cache_data is None:
            print(f"[INFO] No cache found for {self.key}.")
            return None 
        return self.cache_data

    def save_token_to_cache(self, token_info: dict):
        """
        Save the OAuth token to S3.

        Parameters:
            token_info (dict): Spotify OAuth token data.

        Notes:
            AWS Lambda instances are ephemeral. Saving the token to S3 ensures
            future Lambda executions retain the same authenticated session.
        """
        self.cache_data = token_info
        self.s3_manager.save_info(self.bucket, self.key, token_info)