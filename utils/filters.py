import re

# Targeted patterns for live concert cuts, commentary, and filler
FILTER_PATTERNS = [
    # Live concert markers: requires preceding hyphen/parenthesis/bracket, or "Live at/from/in"
    r"(\s*[-–—\(\[]\s*live\b|\blive (at|from|in)\b|\brecorded live\b|\baudiotree\b|\bkexp\b)",
    # Commentary, interviews, skits
    r"\b(commentary|track by track|interview|spoken word|skit|monologue)\b",
    # Backing tracks
    r"\b(karaoke|backing track|minus one)\b",
    # Demos & rough mixes
    r"\b(demo|rehearsal|rough mix|alternate take|alt take)\b",
]

COMPILED_FILTER = re.compile("|".join(FILTER_PATTERNS), re.IGNORECASE)

# Strips edition tags for deduplication, but KEEPS acoustic/reimagined versions distinct
CLEANUP_TAGS = re.compile(
    r"(\s*[-–—]\s*(remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded).*)"
    r"|(\s*[\(\[](remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded|feat\.|with\s).*?[\]\)])",
    re.IGNORECASE,
)


def should_skip(name: str, duration_ms: int | None = None) -> tuple[bool, str]:
    """Returns (should_skip, reason). Reason is empty string if not skipped."""
    match = COMPILED_FILTER.search(name)
    if match:
        return True, f"keyword '{match.group(0).strip()}'"

    # Only drop pure audio fragments under 15 seconds
    if duration_ms is not None and 0 < duration_ms < 15000:
        return True, f"too short ({duration_ms // 1000}s)"

    return False, ""


def normalize_title(title: str) -> str:
    """Safely normalizes titles while preserving acoustic/version distinctions."""
    cleaned = CLEANUP_TAGS.sub("", title).strip()
    return cleaned.lower() if cleaned else title.strip().lower()