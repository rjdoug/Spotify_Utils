from dataclasses import dataclass, field
from pathlib import Path
import config
from utils.client import safe_call
from utils.diagnostics import inspect_playlist_payload, log_drop_event
from utils.filters import normalize_title, should_skip

DEBUG_LOG_PATH = Path("duplicates_debug.log")


@dataclass
class ScrapeStats:
    total_kept: int = 0
    total_filtered: int = 0
    total_duplicates: int = 0
    artist_tracks: dict[str, list[str]] = field(default_factory=dict)


def fetch_source_artists(
    sp, playlist_id: str, debug: bool = False
) -> list[dict]:
    playlist_meta = safe_call(sp.playlist, playlist_id)
    results = safe_call(sp.playlist_items, playlist_id)

    if debug:
        inspect_playlist_payload(playlist_meta, results)

    artists = {}
    while results:
        for item in results.get("items", []):
            track = item.get("item") or item.get("track")
            if track and track.get("artists"):
                for artist in track.get("artists", []):
                    if artist.get("id"):
                        artists[artist["id"]] = artist["name"]

        results = safe_call(sp.next, results) if results.get("next") else None

    return [{"id": k, "name": v} for k, v in artists.items()]


def scrape_artist_discography(
    sp, artist_id: str, artist_name: str = "", debug: bool = False
) -> tuple[list[str], int, int]:
    """Pulls an artist's full tracks using batched album lookups to minimize API calls.

    Returns: (track_uris, filtered_count, duplicate_count)
    """
    track_uris = []
    seen_titles: dict[str, str] = {}
    filtered_count = 0
    duplicate_count = 0

    # 1. Collect all non-skipped release IDs for this artist (paged 10 at a time)
    candidate_album_ids = []
    album_page = safe_call(
        sp.artist_albums,
        artist_id,
        album_type="album,single",
        country=config.MARKET,
        limit=10,
    )

    while album_page:
        for album in album_page.get("items", []):
            album_name = album.get("name", "Unknown Album")
            skip_album, _ = should_skip(album_name)
            if skip_album:
                continue
            if album.get("id"):
                candidate_album_ids.append(album["id"])

        album_page = (
            safe_call(sp.next, album_page) if album_page.get("next") else None
        )

    # 2. Batch-fetch releases in chunks of 20 (Spotify's max for /v1/albums)
    for i in range(0, len(candidate_album_ids), 20):
        batch_ids = candidate_album_ids[i : i + 20]
        albums_payload = safe_call(sp.albums, batch_ids, market=config.MARKET)

        for album_obj in albums_payload.get("albums", []):
            if not album_obj:
                continue

            album_name = album_obj.get("name", "Unknown Album")
            tracks_page = album_obj.get("tracks", {})

            while tracks_page:
                for track in tracks_page.get("items", []):
                    if not track:
                        continue

                    name = track.get("name", "Unknown Track")
                    duration = track.get("duration_ms")

                    # Check hard & short-interlude filters
                    skip_track, skip_reason = should_skip(name, duration)
                    if skip_track:
                        filtered_count += 1
                        if debug:
                            log_drop_event(
                                DEBUG_LOG_PATH,
                                artist_name=artist_name,
                                drop_type="FILTERED",
                                track_name=name,
                                album_name=album_name,
                                reason=skip_reason,
                            )
                        continue

                    # Deduplication check
                    clean_title = normalize_title(name)
                    if clean_title in seen_titles:
                        duplicate_count += 1
                        if debug:
                            log_drop_event(
                                DEBUG_LOG_PATH,
                                artist_name=artist_name,
                                drop_type="DUPLICATE",
                                track_name=name,
                                album_name=album_name,
                                reason=seen_titles[clean_title],
                            )
                        continue

                    seen_titles[clean_title] = f"{name} ({album_name})"
                    track_uris.append(track["uri"])

                # Handle releases with >50 tracks (rare box sets)
                tracks_page = (
                    safe_call(sp.next, tracks_page)
                    if tracks_page.get("next")
                    else None
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