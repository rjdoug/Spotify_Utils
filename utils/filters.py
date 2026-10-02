import re

FILTER_PATTERNS = [
    r"\b(live|live at|live from|live in|recorded live|session|audiotree|kexp|unplugged)\b",
    r"\b(acoustic|acoustic version|stripped)\b",
    r"\b(commentary|track by track|interview|spoken word|skit|monologue)\b",
    r"\b(instrumental|karaoke|backing track|minus one)\b",
    r"\b(demo|rehearsal|rough mix|alternate take|alt take)\b",
]

COMPILED_FILTER = re.compile("|".join(FILTER_PATTERNS), re.IGNORECASE)

# Only strip trailing tags when preceded by ' - ' or enclosed in brackets
CLEANUP_TAGS = re.compile(
    r"(\s*[-–—]\s*(remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded).*)"
    r"|(\s*[\(\[](remaster(ed)?|deluxe|bonus|anniversary|single version|edit|mono|stereo|re-recorded|feat\.|with\s).*?[\]\)])",
    re.IGNORECASE,
)


def should_skip(name: str, duration_ms: int | None = None) -> bool:
    if COMPILED_FILTER.search(name):
        return True
    if duration_ms is not None and duration_ms < 45000:
        return True
    return False


def normalize_title(title: str) -> str:
    """Safely strips remaster/bonus tags without truncating hyphens inside actual song names."""
    cleaned = CLEANUP_TAGS.sub("", title).strip()
    return cleaned.lower() if cleaned else title.strip().lower()