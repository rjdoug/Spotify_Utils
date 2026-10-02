import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from utils.filters import normalize_title, should_skip

load_dotenv()

SOURCE_PLAYLIST_ID = os.getenv("SOURCE_PLAYLIST_ID")
MARKET = os.getenv("SPOTIFY_MARKET", "NZ")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope="playlist-read-private playlist-modify-private playlist-modify-public"
    )
)
user_id = sp.current_user()["id"]


def get_source_artists(playlist_id: str) -> set[str]:
    artist_ids = set()
    results = sp.playlist_items(playlist_id)
    while results:
        for item in results["items"]:
            track = item.get("track")
            if track:
                for artist in track.get("artists", []):
                    artist_ids.add(artist["id"])
        results = sp.next(results) if results["next"] else None
    return artist_ids


def get_artist_tracks(artist_id: str, seen_titles: set[str]) -> list[str]:
    track_uris = []
    albums = sp.artist_albums(
        artist_id, album_type="album,single", country=MARKET, limit=50
    )

    for album in albums["items"]:
        if should_skip(album["name"]):
            continue

        results = sp.album_tracks(album["id"])
        while results:
            for track in results["items"]:
                if should_skip(track["name"], track.get("duration_ms")):
                    continue

                clean_title = normalize_title(track["name"])
                if clean_title and clean_title not in seen_titles:
                    seen_titles.add(clean_title)
                    track_uris.append(track["uri"])

            results = sp.next(results) if results["next"] else None

    return track_uris


def main():
    print("Fetching artists...")
    artist_ids = get_source_artists(SOURCE_PLAYLIST_ID)
    print(f"Found {len(artist_ids)} artists.")

    all_tracks = []
    seen_titles = set()

    for idx, a_id in enumerate(artist_ids, start=1):
        artist = sp.artist(a_id)
        print(f"[{idx}/{len(artist_ids)}] Processing {artist['name']}...")
        all_tracks.extend(get_artist_tracks(a_id, seen_titles))

    print(f"\nCollected {len(all_tracks)} tracks. Building playlist...")

    # Push to Spotify in chunks of 100
    new_playlist = sp.user_playlist_create(
        user=user_id,
        name="Full Discography Discovery",
        public=False,
        description="Auto-generated deep dive discography.",
    )

    for i in range(0, len(all_tracks), 100):
        sp.playlist_add_items(new_playlist["id"], all_tracks[i : i + 100])

    print(f"Done! Playlist ID: {new_playlist['id']}")


if __name__ == "__main__":
    main()