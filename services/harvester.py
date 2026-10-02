from dataclasses import dataclass, field
import config
from utils.client import safe_call
from utils.filters import normalize_title, should_skip


@dataclass
class ScrapeStats:
    total_kept: int = 0
    total_filtered: int = 0
    total_duplicates: int = 0
    artist_tracks: dict[str, list[str]] = field(default_factory=dict)


def fetch_source_artists(sp, playlist_id: str) -> list[dict]:
    """Extracts unique artists from the source playlist."""
    # Query playlist metadata first
    playlist_meta = safe_call(sp.playlist, playlist_id)
    print(f"Target Playlist: '{playlist_meta.get('name')}'")
    print(f"Owner:           {playlist_meta.get('owner', {}).get('display_name')}")
    print(f"Total Tracks:    {playlist_meta.get('tracks', {}).get('total')}")
    print(f"Is Public:       {playlist_meta.get('public')}")
    print(f"Is Collaborative:{playlist_meta.get('collaborative')}\n")

    artists = {}
    results = safe_call(sp.playlist_items, playlist_id)

    while results:
        for item in results.get("items", []):
            track = item.get("track")
            if track:
                for artist in track.get("artists", []):
                    artists[artist["id"]] = artist["name"]
        results = safe_call(sp.next, results) if results.get("next") else None

    return [{"id": k, "name": v} for k, v in artists.items()]


def scrape_artist_discography(
    sp, artist_id: str
) -> tuple[list[str], int, int]:
    """Pulls an artist's full tracks, isolating deduplication to this artist alone.

    Returns: (track_uris, filtered_count, duplicate_count)
    """
    track_uris = []
    seen_titles = set()
    filtered_count = 0
    duplicate_count = 0

    albums = safe_call(
        sp.artist_albums,
        artist_id,
        album_type="album,single",
        country=config.MARKET,
        limit=50,
    )

    for album in albums.get("items", []):
        if should_skip(album["name"]):
            continue

        results = safe_call(sp.album_tracks, album["id"])
        while results:
            for track in results.get("items", []):
                name = track["name"]
                duration = track.get("duration_ms")

                if should_skip(name, duration):
                    filtered_count += 1
                    continue

                clean_title = normalize_title(name)
                if clean_title in seen_titles:
                    duplicate_count += 1
                    continue

                seen_titles.add(clean_title)
                track_uris.append(track["uri"])

            results = (
                safe_call(sp.next, results) if results.get("next") else None
            )

    return track_uris, filtered_count, duplicate_count


def create_discovery_playlists(
    sp, user_id: str, track_uris: list[str], base_name: str
):
    """Splits collected tracks into 10,000-track playlists and uploads in batches of 100."""
    chunks = [
        track_uris[i : i + config.MAX_PLAYLIST_SIZE]
        for i in range(0, len(track_uris), config.MAX_PLAYLIST_SIZE)
    ]

    for idx, chunk in enumerate(chunks, start=1):
        suffix = f" (Part {idx})" if len(chunks) > 1 else ""
        playlist_name = f"{base_name}{suffix}"

        print(f"\nCreating playlist: '{playlist_name}'...")
        playlist = safe_call(
            sp.user_playlist_create,
            user=user_id,
            name=playlist_name,
            public=False,
            description="Auto-generated deep dive discography.",
        )

        for i in range(0, len(chunk), config.BATCH_ADD_SIZE):
            batch = chunk[i : i + config.BATCH_ADD_SIZE]
            safe_call(sp.playlist_add_items, playlist["id"], batch)

        print(f"Created: {playlist['id']} ({len(chunk)} tracks added)")