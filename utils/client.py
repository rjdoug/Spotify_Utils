import time
from typing import Any, Callable
import requests
from requests.adapters import HTTPAdapter
import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from urllib3.util import Retry


def get_spotify_client() -> spotipy.Spotify:
    """Builds a Spotify client equipped with automatic exponential backoff

    and strict Retry-After header enforcement.
    """
    session = requests.Session()

    # Retry strategy for transient connection errors and rate limits
    retry_strategy = Retry(
        total=10,
        backoff_factor=1.5,  # Sleeps 1.5s, 3s, 6s... between attempts
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,  # Pauses for Spotify's exact Retry-After duration
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-read-private playlist-modify-private playlist-modify-public"
        ),
        requests_session=session,
    )


def safe_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Wrapper that catches any unhandled 429s and gracefully sleeps

    instead of terminating the entire program.
    """
    while True:
        try:
            # Small proactive breathing room (30ms) to reduce 429 triggers
            time.sleep(0.03)
            return func(*args, **kwargs)
        except SpotifyException as exc:
            if exc.http_status == 429:
                wait_seconds = int(
                    exc.headers.get("Retry-After", 5)
                ) if exc.headers else 5
                print(
                    f"\n[Rate Limit] Spotify requested backoff. Sleeping for {wait_seconds}s..."
                )
                time.sleep(wait_seconds + 1)
            else:
                raise exc