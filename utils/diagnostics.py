import json
from pathlib import Path


def log_drop_event(
    log_file: Path,
    artist_name: str,
    drop_type: str,
    track_name: str,
    album_name: str,
    conflicted_with: str = "",
):
    """Appends dropped track details directly to a log file with instant flushing."""
    with open(log_file, "a", encoding="utf-8") as f:
        if drop_type == "DUPLICATE":
            f.write(
                f"[DUPLICATE] {artist_name} | '{track_name}' ({album_name}) -> matches '{conflicted_with}'\n"
            )
        elif drop_type == "FILTERED":
            f.write(
                f"[FILTERED]  {artist_name} | '{track_name}' ({album_name}) -> matched rejection keyword\n"
            )
        f.flush()

def inspect_playlist_payload(
    playlist_meta: dict, items_raw: dict, dump_file: str = ".debug_playlist.json"
):
    """Outputs a clean structural summary and dumps raw JSON to an inspection file."""
    print("\n" + "=" * 20 + " DEBUG INSPECTION " + "=" * 20)

    # 1. Inspect playlist metadata
    print("Playlist Metadata Keys:", list(playlist_meta.keys()))
    tracks_meta = playlist_meta.get("tracks")
    print(f"playlist['tracks'] Type: {type(tracks_meta).__name__}")
    if isinstance(tracks_meta, dict):
        print(f"playlist['tracks'] Keys: {list(tracks_meta.keys())}")
        print(f"playlist['tracks']['total']: {tracks_meta.get('total')}")

    # 2. Inspect playlist_items endpoint payload
    print("\nPlaylist Items Call:")
    print("items_raw Keys:", list(items_raw.keys()))
    items = items_raw.get("items", [])
    print(f"Total reported by endpoint: {items_raw.get('total')}")
    print(f"Items array length in page 1: {len(items)}")

    # 3. Check sample item structure if items exist
    if items:
        first = items[0]
        track_obj = first.get("track") or first.get("item")
        print("\nSample Item[0]:")
        print(f"  Wrapper keys: {list(first.keys())}")
        print(f"  'track' is None: {track_obj is None}")
        if track_obj:
            print(f"  Track Name: {track_obj.get('name')}")
            print(f"  Track Type: {track_obj.get('type')}")
            print(
                f"  Artists: {[a.get('name') for a in track_obj.get('artists', [])]}"
            )
    else:
        print("\n[!] The 'items' array returned from Spotify is completely empty.")

    # 4. Dump full raw responses to a local JSON file for inspection
    debug_data = {"playlist_meta": playlist_meta, "items_page_1": items_raw}

    debug_path = Path(dump_file)
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)

    print(f"\nFull raw response written to: {debug_path.resolve()}")
    print("=" * 58 + "\n")