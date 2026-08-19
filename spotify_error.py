class InvalidGrantError(Exception):
    def __init__(self, user_id: str):
        super().__init__(
            f"User '{user_id}' must reauthenticate with Spotify. Run spotify_auth.py with an owner id"
        )