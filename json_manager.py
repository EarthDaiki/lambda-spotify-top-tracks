class JsonManager:
    """
    This class is responsible for handling JSON structures used by the
    AWS Lambda Spotify project. It provides helper methods
    for checking whether a user already exists in the JSON data and for
    creating default structures for new users.
    """

    def __init__(self):
        """
        Even though the constructor does not currently perform initialization,
        it is included for consistency and future scalability.
        """
        pass

    def make_new_user(self, data: dict, user_id: str) -> dict:
        """
        Create a new user entry inside the playlist metadata JSON.

        Parameters:
            data (dict): Empty playlist uris dict.
            user_id (str): The ID of the user being processed.

        Returns:
            dict: Updated dictionary including a newly added user structure.

        Notes:
            This method is used when the Lambda function determines that
            a Spotify user has no existing playlist URI data stored in S3.
            It initializes empty placeholders for:
              - current_user_top_tracks_uris
              - artist_top_tracks_uris
            across all Spotify time ranges (short, medium, long).
        """
        data[user_id] = {
            "current_user_top_tracks_uris": {
                "short_term": '',
                "medium_term": '',
                "long_term": ''
            },
            "artist_top_tracks_uris": {
                "short_term": '',
                "medium_term": '',
                "long_term": ''
            }
        }
        return data
    
    def is_new_user(self, data: dict, user_id: str) -> bool:
        """
        Check whether the given user_id exists in playlist uris json file.

        Parameters:
            data (dict): The dictionary containing playlist uris.
            user_id (str): A user identifier (not required to be the actual Spotify user ID;
                           any unique ID is acceptable).

        Returns:
            bool: True if the user does not exist in the playlist uris json file (i.e., new user),
                  False otherwise.

        Notes:
            This function is used by SpotifyMain to determine whether a user
            needs initial playlist structures created and uploaded to S3.
        """
        return user_id not in data