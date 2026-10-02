import sys
import time
from typing import Any, Callable
import requests
from requests.adapters import HTTPAdapter
import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from urllib3.util import Retry


def get_spotify_client() -> spotipy.Spotify:
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
        respect_retry_after_header=True,
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
    """Executes a Spotify API call with automatic rate-limit recovery

    and readable terminal diagnostics for common HTTP failures.
    """
    while True:
        try:
            time.sleep(0.03)  # Gentle spacing between calls
            return func(*args, **kwargs)

        except SpotifyException as exc:
            # 429: Rate limited
            if exc.http_status == 429:
                wait_sec = int(
                    exc.headers.get("Retry-After", 5)
                ) if exc.headers else 5
                print(
                    f"\n[Rate Limit] Spotify requested cooldown. Pausing for {wait_sec}s..."
                )
                time.sleep(wait_sec + 1)
                continue

            # 400: Malformed ID or request
            if exc.http_status == 400:
                print("\n[Spotify Error 400: Bad Request]")
                print("-> The Spotify API could not recognize the resource ID.")
                print(
                    f"-> Details: {exc.msg if hasattr(exc, 'msg') else exc}"
                )
                sys.exit(1)

            # 401 / 403: Bad credentials or missing playlist permissions
            if exc.http_status in (401, 403):
                print(
                    f"\n[Spotify Error {exc.http_status}: Authentication/Forbidden]"
                )
                print(
                    "-> Check that your Client ID & Secret are valid, or delete '.cache' to re-authenticate."
                )
                sys.exit(1)

            # 404: Playlist or artist doesn't exist
            if exc.http_status == 404:
                print("\n[Spotify Error 404: Not Found]")
                print(
                    "-> Could not find the requested playlist. Make sure it isn't set to private on an unrelated account."
                )
                sys.exit(1)

            # Any other unexpected Spotify exception
            print(f"\n[Spotify API Error {exc.http_status}] {exc}")
            sys.exit(1)

        except requests.exceptions.ConnectionError:
            print("\n[Network Error] Lost connection to Spotify servers.")
            print("-> Please check your internet connection and try again.")
            sys.exit(1)