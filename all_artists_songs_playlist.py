import argparse
import json
from pathlib import Path
import config
from services.harvester import (
    create_discovery_playlists,
    fetch_source_artists,
    scrape_artist_discography,
)
from utils.client import get_spotify_client, safe_call

CHECKPOINT_FILE = Path("progress_checkpoint.json")


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
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore and wipe existing progress checkpoint to start completely over.",
    )
    return parser.parse_args()


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_checkpoint(
    completed_ids: list[str],
    all_tracks: list[str],
    total_filtered: int,
    total_dupes: int,
):
    tmp_path = CHECKPOINT_FILE.with_suffix(".tmp")
    data = {
        "completed_ids": completed_ids,
        "all_tracks": all_tracks,
        "total_filtered": total_filtered,
        "total_dupes": total_dupes,
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp_path.replace(CHECKPOINT_FILE)


def main():
    args = parse_args()
    sp = get_spotify_client()
    user_id = safe_call(sp.current_user)["id"]

    if args.dry_run:
        print("=== DRY RUN MODE: No playlists will be created ===\n")

    if args.fresh and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print("[Checkpoint] Wiped previous checkpoint (--fresh).\n")

    log_file = Path("duplicates_debug.log")
    if args.debug and not CHECKPOINT_FILE.exists() and log_file.exists():
        log_file.unlink()

    print("Fetching artists from source playlist...")
    artists = fetch_source_artists(
        sp, config.SOURCE_PLAYLIST_ID, debug=args.debug
    )
    print(f"Found {len(artists)} unique artists.\n")

    # Load checkpoint data if available
    checkpoint = load_checkpoint()
    completed_ids = set(checkpoint.get("completed_ids", []))
    all_tracks = checkpoint.get("all_tracks", [])
    total_filtered = checkpoint.get("total_filtered", 0)
    total_dupes = checkpoint.get("total_dupes", 0)

    if completed_ids:
        print(
            f"[Checkpoint] Resuming run: {len(completed_ids)}/{len(artists)} artists already completed "
            f"({len(all_tracks)} tracks in memory).\n"
        )

    for idx, artist in enumerate(artists, start=1):
        if artist["id"] in completed_ids:
            continue

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
        completed_ids.add(artist["id"])

        print(
            f"{len(tracks)} kept | {filtered_cnt} filtered | {dupe_cnt} duplicates dropped",
            flush=True,
        )

        # Save checkpoint after every completed artist
        save_checkpoint(
            list(completed_ids), all_tracks, total_filtered, total_dupes
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
        print("[Dry Run] Finished cleanly. Checkpoint saved for live run.")
        return

    create_discovery_playlists(
        sp,
        user_id=user_id,
        track_uris=all_tracks,
        base_name=args.name,
    )

    # Clean up checkpoint only after successful playlist upload
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print("\n[Done] Checkpoint cleaned up.")


if __name__ == "__main__":
    main()