import json
from pathlib import Path


def inspect_playlist_payload(
    playlist_meta: dict, items_raw: dict, dump_file: str = ".debug_playlist.json"
):
    print("\n" + "=" * 20 + " DEBUG INSPECTION " + "=" * 20)
    print("Playlist Metadata Keys:", list(playlist_meta.keys()))

    items = items_raw.get("items", [])
    print(f"Total reported by endpoint: {items_raw.get('total')}")
    print(f"Items array length in page 1: {len(items)}")

    debug_data = {"playlist_meta": playlist_meta, "items_page_1": items_raw}
    debug_path = Path(dump_file)
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)

    print(f"\nFull raw response written to: {debug_path.resolve()}")
    print("=" * 58 + "\n")


def log_drop_event(
    log_file: Path,
    artist_name: str,
    drop_type: str,
    track_name: str,
    album_name: str,
    reason: str = "",
):
    """Appends dropped track details directly to disk with instant flushing."""
    with open(log_file, "a", encoding="utf-8") as f:
        if drop_type == "DUPLICATE":
            f.write(
                f"[DUPLICATE] {artist_name} | '{track_name}' ({album_name}) -> matches '{reason}'\n"
            )
        elif drop_type == "FILTERED":
            f.write(
                f"[FILTERED]  {artist_name} | '{track_name}' ({album_name}) -> {reason}\n"
            )
        f.flush()