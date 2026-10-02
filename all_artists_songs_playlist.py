import os
from dotenv import load_dotenv
from utils.client import get_spotify_client, safe_call
from utils.filters import normalize_title, should_skip

load_dotenv()

SOURCE_PLAYLIST_ID = os.getenv("SOURCE_PLAYLIST_ID")
MARKET = os.getenv("SPOTIFY_MARKET", "NZ")

sp = get_spotify_client()
user_id = safe_call(sp.current_user)["id"]


def get_source_artists(playlist_id: str) -> set[str]:
    artist_ids = set()
    results = safe_call(sp.playlist_items, playlist_id)
    while results:
        for item in results.get("items", []):
            track = item.get("track")
            if track:
                for artist in track.get("artists", []):
                    artist_ids.add(artist["id"])
        results = safe_call(sp.next, results) if results.get("next") else None
    return artist_ids


def get_artist_tracks(artist_id: str) -> list[str]:
    track_uris = []
    # Scoped strictly to this artist so other artists' matching titles are not dropped
    seen_titles = set()

    albums = safe_call(
        sp.artist_albums,
        artist_id,
        album_type="album,single",
        country=MARKET,
        limit=50,
    )

    for album in albums.get("items", []):
        if should_skip(album["name"]):
            continue

        results = safe_call(sp.album_tracks, album["id"])
        while results:
            for track in results.get("items", []):
                if should_skip(track["name"], track.get("duration_ms")):
                    continue

                clean_title = normalize_title(track["name"])
                if clean_title and clean_title not in seen_titles:
                    seen_titles.add(clean_title)
                    track_uris.append(track["uri"])

            results = (
                safe_call(sp.next, results) if results.get("next") else None
            )

    return track_uris


def main():
    print("Fetching artists...")
    artist_ids = get_source_artists(SOURCE_PLAYLIST_ID)
    print(f"Found {len(artist_ids)} artists.")

    all_tracks = []

    for idx, a_id in enumerate(artist_ids, start=1):
        artist = safe_call(sp.artist, a_id)
        print(f"[{idx}/{len(artist_ids)}] Processing {artist['name']}...")

        # Each artist runs through their own local de-duplication
        tracks = get_artist_tracks(a_id)
        all_tracks.extend(tracks)

    print(f"\nCollected {len(all_tracks)} tracks. Building playlist...")

    new_playlist = safe_call(
        sp.user_playlist_create,
        user=user_id,
        name="Full Discography Discovery",
        public=False,
        description="Auto-generated deep dive discography.",
    )

    for i in range(0, len(all_tracks), 100):
        safe_call(sp.playlist_add_items, new_playlist["id"], all_tracks[i : i + 100])

    print(f"Done! Playlist ID: {new_playlist['id']}")


if __name__ == "__main__":
    main()