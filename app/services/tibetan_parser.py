import re
import json
import asyncio
import httpx
from typing import List, Tuple, Dict
from app.config import get_settings

settings = get_settings()

SEGMENT_PROMPT = """Analyze this Tibetan text and split it into meaningful phrases/words based on Tibetan grammar and context. Each phrase should be a complete semantic unit (like a word, compound word, or short phrase that makes sense together).

Tibetan text:
{text}

Return ONLY a valid JSON array of objects with NO markdown formatting. Each object should have:
- "tibetan": the Tibetan phrase exactly as it appears in the text (with tsheg ་ between syllables if part of the same word)
- "order": the position in the text (0-indexed)

Important:
- Keep compound words and names together (e.g., ཨོ་རྒྱན should be one phrase, not split)
- Honorific prefixes should stay with their words (e.g., བཀུར་བ should stay together)
- Common phrases that form semantic units should be grouped

Example output: [{"tibetan": "བཀྲ་ཤིས་བདེ་ལེགས", "order": 0}, {"tibetan": "ཞུ་བ་ཡིན", "order": 1}]"""


async def segment_tibetan_text_async(text: str) -> List[Tuple[int, str]]:
    """
    Use AI to intelligently segment Tibetan text into meaningful phrases.
    Returns list of (order, phrase) tuples.
    """
    text = text.strip()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.anthropic_base_url}/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_auth_token,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 2048,
                    "messages": [
                        {"role": "user", "content": SEGMENT_PROMPT.format(text=text)}
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return parse_segment_response(content)
            else:
                # Fallback to simple tsheg splitting
                return fallback_extract(text)

        except Exception as e:
            print(f"Error segmenting text: {e}")
            return fallback_extract(text)


def parse_segment_response(content: str) -> List[Tuple[int, str]]:
    """
    Parse the JSON response from the segmentation API.
    """
    try:
        # Clean up the response
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        content = content.strip()

        parsed = json.loads(content)

        if isinstance(parsed, list):
            phrases = []
            seen = set()
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                tibetan = item.get("tibetan", "")
                order = item.get("order", len(phrases))

                if tibetan and tibetan not in seen:
                    phrases.append((order, tibetan))
                    seen.add(tibetan)

            # Sort by order
            phrases.sort(key=lambda x: x[0])
            return phrases

        return []

    except json.JSONDecodeError:
        return []


def fallback_extract(text: str) -> List[Tuple[int, str]]:
    """
    Fallback extraction using tsheg delimiter when AI is unavailable.
    """
    text = text.strip()
    raw_words = re.split(r'[་། །\s]+', text)

    words = []
    seen = set()
    order = 0

    for word in raw_words:
        if not word:
            continue
        cleaned = re.sub(r'[^\u0F00-\u0FFF]', '', word)
        if cleaned and cleaned not in seen:
            words.append((order, cleaned))
            seen.add(cleaned)
            order += 1

    return words


def extract_tibetan_words(text: str) -> List[Tuple[int, str]]:
    """
    Extract Tibetan phrases from text using AI-based segmentation.
    Sync wrapper for async function.

    Returns list of (order, phrase) tuples.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context, create new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, segment_tibetan_text_async(text))
                return future.result()
        else:
            return loop.run_until_complete(segment_tibetan_text_async(text))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(segment_tibetan_text_async(text))


def get_title_from_text(text: str, max_words: int = 5) -> str:
    """
    Generate a title from the first few phrases of Tibetan text.
    """
    words = extract_tibetan_words(text)
    title_words = [w for _, w in words[:max_words]]
    return '་'.join(title_words) if title_words else "无标题"
