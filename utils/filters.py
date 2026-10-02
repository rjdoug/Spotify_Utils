import re

# Word-boundary patterns targeting bonus/fluff cuts
FILTER_PATTERNS = [
    # Live recordings
    r"\b(live|live at|live from|live in|recorded live|session|audiotree|kexp|unplugged)\b",
    # Acoustic / stripped versions
    r"\b(acoustic|acoustic version|stripped)\b",
    # Commentary, interviews, spoken skits
    r"\b(commentary|track by track|interview|spoken word|skit|monologue)\b",
    # Instrumental / backing / karaoke cuts
    r"\b(instrumental|karaoke|backing track|minus one)\b",
    # Demos & alternate takes
    r"\b(demo|rehearsal|rough mix|alternate take|alt take)\b",
]

COMPILED_FILTER = re.compile("|".join(FILTER_PATTERNS), re.IGNORECASE)


def should_skip(name: str, duration_ms: int | None = None) -> bool:
    """Evaluates whether an album or track name meets rejection criteria."""
    if COMPILED_FILTER.search(name):
        return True

    # Drop skits / interludes under 45 seconds
    if duration_ms is not None and duration_ms < 45000:
        return True

    return False


def normalize_title(title: str) -> str:
    """Strips remaster tags, parentheticals, and extra punctuation to prevent duplicates.

    Example: 'Song Title - Remastered 2021' -> 'song title'
    """
    cleaned = re.sub(r"(\(|\[|-).*", "", title)
    return cleaned.strip().lower()