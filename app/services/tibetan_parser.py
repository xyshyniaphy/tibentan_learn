import re
from typing import List, Tuple


def extract_tibetan_words(text: str) -> List[Tuple[int, str]]:
    """
    Extract Tibetan words from text using tsheg (་) delimiter.

    Returns list of (order, word) tuples.
    """
    # Tibetan Unicode range: U+0F00 to U+0FFF
    # Tsheg delimiter: ་ (U+0F0B)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Split by tsheg and other common delimiters
    # Tsheg: ་, Shey: །, space
    raw_words = re.split(r'[་། །\s]+', text)

    words = []
    seen = set()
    order = 0

    for word in raw_words:
        # Skip empty strings
        if not word:
            continue

        # Clean the word - remove any non-Tibetan characters
        cleaned = re.sub(r'[^\u0F00-\u0FFF]', '', word)

        if cleaned and cleaned not in seen:
            words.append((order, cleaned))
            seen.add(cleaned)
            order += 1

    return words


def get_title_from_text(text: str, max_words: int = 5) -> str:
    """
    Generate a title from the first few words of Tibetan text.
    """
    words = extract_tibetan_words(text)
    title_words = [w for _, w in words[:max_words]]
    return '་'.join(title_words) if title_words else "Untitled"
