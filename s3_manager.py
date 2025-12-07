import json
import boto3
from typing import Optional, Dict, Any

class S3Manager:
    """
    Wrapper class for loading and saving JSON files in AWS S3.
    This is used by the Spotify Lambda workflow to manage:
    - users name json file (USERS_FILE_KEY)
    - playlist uris data json file (PLAYLIST_INFO_FILE_KEY)
    - token cache files (.cache-{user_id})
    """
    def __init__(self):
        '''
        Using boto3 client for S3 operations inside AWS Lambda
        '''
        self.s3 = boto3.client("s3")

    def load_info(self, bucket_name: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Loads a JSON file from S3 and returns it as a Python dict.
        Returns an empty dict if the file does not exist.
        """
        try:
            obj = self.s3.get_object(Bucket=bucket_name, Key=key)
            data = obj["Body"].read().decode("utf-8")
            return json.loads(data)
        except self.s3.exceptions.NoSuchKey:
            print("No cache found in S3.")
            return {}

    def save_info(self, bucket_name: str, key: str, data: dict):
        """
        Saves a Python dict to S3 as a JSON file.
        """
        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(data, ensure_ascii=False, indent=4),
                ContentType="application/json"
            )
        except self.s3.exceptions.NoSuchKey:
            print("NoSuchKey. Data could not save.")