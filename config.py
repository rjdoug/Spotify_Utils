import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_PLAYLIST_ID = os.getenv("SOURCE_PLAYLIST_ID")
MARKET = os.getenv("SPOTIFY_MARKET", "NZ")
MAX_PLAYLIST_SIZE = 10000
BATCH_ADD_SIZE = 100

if not os.getenv("SPOTIPY_CLIENT_ID") or not os.getenv("SPOTIPY_CLIENT_SECRET"):
    raise ValueError("Missing Spotify API credentials in .env file.")

if not SOURCE_PLAYLIST_ID:
    raise ValueError("Missing SOURCE_PLAYLIST_ID in .env file.")