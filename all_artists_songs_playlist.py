import argparse
from pathlib import Path
import config
from services.harvester import (
    create_discovery_playlists,
    fetch_source_artists,
    scrape_artist_discography,
)
from utils.client import get_spotify_client, safe_call


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape artist discographies from a playlist into an ultimate queue."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the scrape without creating playlists.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print structural diagnostics and stream dropped tracks to duplicates_debug.log.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="Full Discography Discovery",
        help="Custom base name for the generated playlist(s).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    sp = get_spotify_client()
    user_id = safe_call(sp.current_user)["id"]

    if args.dry_run:
        print("=== DRY RUN MODE: No playlists will be created ===\n")

    log_file = Path("duplicates_debug.log")
    if args.debug and log_file.exists():
        log_file.unlink()

    print("Fetching artists from source playlist...")
    artists = fetch_source_artists(
        sp, config.SOURCE_PLAYLIST_ID, debug=args.debug
    )
    print(f"Found {len(artists)} unique artists.\n")

    all_tracks = []
    total_filtered = 0
    total_dupes = 0

    for idx, artist in enumerate(artists, start=1):
        print(
            f"[{idx}/{len(artists)}] {artist['name']}... ",
            end="",
            flush=True,
        )

        tracks, filtered_cnt, dupe_cnt = scrape_artist_discography(
            sp,
            artist["id"],
            artist_name=artist["name"],
            debug=args.debug,
        )
        all_tracks.extend(tracks)
        total_filtered += filtered_cnt
        total_dupes += dupe_cnt

        print(
            f"{len(tracks)} kept | {filtered_cnt} filtered | {dupe_cnt} duplicates dropped",
            flush=True,
        )

    print("\n" + "=" * 45)
    print("HARVEST SUMMARY")
    print(f"Total tracks collected:   {len(all_tracks)}")
    print(f"Total tracks filtered:    {total_filtered}")
    print(f"Total duplicates dropped: {total_dupes}")
    print("=" * 45)

    if args.dry_run:
        playlists_needed = (len(all_tracks) // config.MAX_PLAYLIST_SIZE) + 1
        print(f"\n[Dry Run] Would generate {playlists_needed} playlist(s).")
        print("[Dry Run] Finished cleanly.")
        return

    create_discovery_playlists(
        sp,
        user_id=user_id,
        track_uris=all_tracks,
        base_name=args.name,
    )


if __name__ == "__main__":
    main()