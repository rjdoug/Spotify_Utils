import os
import re
import sys
from dotenv import load_dotenv

load_dotenv()


def extract_clean_id(raw_value: str | None, entity_name: str) -> str:
    """Cleans URLs, URIs, and query strings down to Spotify's standard 22-character ID.

    Exits with a friendly CLI message if invalid.
    """
    if not raw_value:
        print(f"\n[Config Error] Missing {entity_name} in your .env file.")
        print(f"-> Add {entity_name}=<your_id> to .env and try again.\n")
        sys.exit(1)

    cleaned = raw_value.strip("\"' \t\n\r")

    # Handle full web URL: https://open.spotify.com/playlist/<id>?si=...
    if "spotify.com/" in cleaned:
        cleaned = cleaned.split("/")[-1].split("?")[0].split("#")[0]
    # Handle URI: spotify:playlist:<id>
    elif cleaned.startswith("spotify:"):
        cleaned = cleaned.split(":")[-1]
    # Handle leftover query parameters
    else:
        cleaned = cleaned.split("?")[0].split("#")[0]

    # Spotify IDs are strictly 22 alphanumeric characters
    if not re.match(r"^[0-9A-Za-z]{22}$", cleaned):
        print(
            f"\n[Config Error] Invalid {entity_name}: '{raw_value.strip()}'"
        )
        print(
            "-> Expected a 22-character Spotify ID (or standard playlist link)."
        )
        print(
            "-> Make sure trailing parameters like '?si=...' are removed.\n"
        )
        sys.exit(1)

    return cleaned


# Credentials check
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("\n[Auth Error] Missing Spotify Developer Credentials.")
    print("-> Ensure SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET exist in .env")
    print(
        "-> Get them at: https://developer.spotify.com/dashboard/applications\n"
    )
    sys.exit(1)

SOURCE_PLAYLIST_ID = extract_clean_id(
    os.getenv("SOURCE_PLAYLIST_ID"), "SOURCE_PLAYLIST_ID"
)
MARKET = os.getenv("SPOTIFY_MARKET", "NZ")
MAX_PLAYLIST_SIZE = 10000
BATCH_ADD_SIZE = 100