import re
from typing import List, Optional

def parse_args_safe(text: str, min_args: int = 0) -> Optional[List[str]]:
    """
    Parse arguments from a Telegram command message text.

    Args:
        text: The full message text (e.g. "/cl 12345").
        min_args: Minimum number of arguments required.

    Returns:
        List of arguments if enough provided, else None.
    """
    if not text:
        return None

    # Replace non-breaking spaces with normal space, trim
    clean = text.replace("\u00A0", " ").strip()

    # Split by whitespace
    parts = re.split(r"\s+", clean)

    # Skip the command itself (parts[0])
    args = parts[1:]

    return args if len(args) >= min_args else None


def clean_id(s: str) -> str:
    """
    Clean a club ID by removing '#' prefix, commas, and extra whitespace.
    """
    return s.lstrip("#").replace(",", "").strip()
