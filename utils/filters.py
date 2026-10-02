import re

# 1. Hard filters: live concerts, commentary, and karaoke/backing versions
HARD_FILTER_PATTERNS = [
    # Live concert markers: requires preceding separator or "Live at/from/in"
    r"(\s*[-–—\(\[]\s*live\b|\blive (at|from|in)\b|\brecorded live\b|\baudiotree\b|\bkexp\b)",
    # Commentary, interviews, spoken skits
    r"\b(commentary|track by track|interview|spoken word|monologue)\b",
    # Karaoke / explicit backing instrumental versions
    r"\b(karaoke|backing track|minus one|instrumental version)\b",
    # Demos & rough mixes
    r"\b(demo|rehearsal|rough mix|alternate take|alt take)\b",
]

# 2. Soft filters: only skipped if the track is ALSO under 60 seconds
SHORT_INTERLUDE_PATTERNS = [
    r"\b(intro|outro|interlude|skit|instrumental)\b",
]

COMPILED_HARD = re.compile("|".join(HARD_FILTER_PATTERNS), re.IGNORECASE)
COMPILED_SHORT = re.compile("|".join(SHORT_INTERLUDE_PATTERNS), re.IGNORECASE)

# Strips edition tags for deduplication, but preserves acoustic versions
CLEANUP_TAGS = re.compile(
    r"(\s*[-–—]\s*(remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded).*)"
    r"|(\s*[\(\[](remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded|feat\.|with\s).*?[\]\)])",
    re.IGNORECASE,
)


def should_skip(name: str, duration_ms: int | None = None) -> tuple[bool, str]:
    """Returns (should_skip, reason)."""
    # Check hard filters (live, demo, commentary)
    hard_match = COMPILED_HARD.search(name)
    if hard_match:
        return True, f"matched '{hard_match.group(0).strip()}'"

    # Check soft filters: only drop if it matches an interlude tag AND is under 60 seconds
    if duration_ms is not None and duration_ms < 60000:
        short_match = COMPILED_SHORT.search(name)
        if short_match:
            return (
                True,
                f"short {short_match.group(0).strip()} ({duration_ms // 1000}s < 60s)",
            )

    # Micro-fragments under 10 seconds (silent gaps, audio glitch clips)
    if duration_ms is not None and 0 < duration_ms < 10000:
        return True, f"audio fragment ({duration_ms // 1000}s)"

    return False, ""


def normalize_title(title: str) -> str:
    """Safely normalizes titles while preserving acoustic distinctions."""
    cleaned = CLEANUP_TAGS.sub("", title).strip()
    return cleaned.lower() if cleaned else title.strip().lower()