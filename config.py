import os
import re
from dotenv import load_dotenv

load_dotenv()


def clean_spotify_id(raw_id: str | None) -> str:
    if not raw_id:
        return ""
    # Strip quotes and surrounding whitespace
    cleaned = raw_id.strip("\"' \t\n\r")

    # If full URL: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...
    if "/playlist/" in cleaned:
        cleaned = cleaned.split("/playlist/")[1].split("?")[0]

    # If URI: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    elif cleaned.startswith("spotify:playlist:"):
        cleaned = cleaned.split(":")[-1]

    # Clean any leftover query params or anchors
    cleaned = cleaned.split("?")[0].split("#")[0]
    return cleaned


RAW_PLAYLIST_ID = os.getenv("SOURCE_PLAYLIST_ID")
SOURCE_PLAYLIST_ID = clean_spotify_id(RAW_PLAYLIST_ID)
MARKET = os.getenv("SPOTIFY_MARKET", "NZ")
MAX_PLAYLIST_SIZE = 10000
BATCH_ADD_SIZE = 100

if not os.getenv("SPOTIPY_CLIENT_ID") or not os.getenv("SPOTIPY_CLIENT_SECRET"):
    raise ValueError("Missing Spotify API credentials in .env file.")

if not SOURCE_PLAYLIST_ID:
    raise ValueError(
        "Missing or invalid SOURCE_PLAYLIST_ID in .env file. Please check your link/ID."
    )