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
    # Retry transient 5xx server drops, but do NOT let urllib3 sleep silently on 429
    retry_strategy = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        respect_retry_after_header=False,
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
        requests_timeout=10,  # Never hang on dead sockets
        retries=0,           # Disable Spotipy's silent internal sleep on 429
        status_retries=0,
    )


def safe_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Executes Spotify API calls with 0.15s pacing, visible cooldown timers, and network recovery."""
    while True:
        try:
            time.sleep(0.15)  # Safe pacing to prevent tripping rate limits
            return func(*args, **kwargs)

        except SpotifyException as exc:
            # 429: Rate limited - Display an active countdown on screen
            if exc.http_status == 429:
                wait_sec = (
                    int(exc.headers.get("Retry-After", 5))
                    if exc.headers
                    else 5
                )
                print(
                    f"\n[Rate Limit] Spotify requested cooldown ({wait_sec}s).",
                    flush=True,
                )
                for remaining in range(wait_sec, 0, -1):
                    print(
                        f"  -> Resuming in {remaining}s...   \r",
                        end="",
                        flush=True,
                    )
                    time.sleep(1)
                print("\n  -> Resuming scrape now...\n", flush=True)
                continue

            # 400: Malformed ID or query validation error
            if exc.http_status == 400:
                print("\n[Spotify Error 400: Bad Request]")
                print(f"-> Details: {exc.msg if hasattr(exc, 'msg') else exc}")
                sys.exit(1)

            # 401 / 403: Bad credentials or expired session
            if exc.http_status in (401, 403):
                print(
                    f"\n[Spotify Error {exc.http_status}: Authentication/Forbidden]"
                )
                print(
                    "-> Check your Client ID & Secret in .env, or delete '.cache' to re-authenticate."
                )
                sys.exit(1)

            # 404: Playlist or artist doesn't exist
            if exc.http_status == 404:
                print("\n[Spotify Error 404: Not Found]")
                print(
                    "-> Could not find the requested resource. Verify your SOURCE_PLAYLIST_ID."
                )
                sys.exit(1)

            print(f"\n[Spotify API Error {exc.http_status}] {exc}")
            sys.exit(1)

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            print(
                "\n[Network Delay] Connection timed out. Retrying in 2s...",
                flush=True,
            )
            time.sleep(2)
            continue