import re
import json
import asyncio
import httpx
from typing import List, Tuple, Dict
from app.config import get_settings

settings = get_settings()

PROCESS_PROMPT = """Analyze this Tibetan text and extract meaningful phrases with translations.

For each phrase:
- Keep compound words and names together (e.g., ཨོ་རྒྱན is ONE phrase, not split)
- Group syllables that form semantic units together
- Honorific prefixes should stay with their words

Return ONLY a valid JSON array with NO markdown formatting:
[{"tibetan": "phrase", "phonetic": "romanization", "chinese": "中文翻译", "english": "translation", "order": 0}]

Tibetan text:
{text}"""


async def process_tibetan_text_async(text: str) -> List[Dict]:
    """
    Use AI to segment and translate Tibetan text in one step.
    Returns list of translation dictionaries.
    """
    text = text.strip()

    async with httpx.AsyncClient(timeout=120.0) as client:
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
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": PROCESS_PROMPT.format(text=text)}
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return parse_process_response(content)
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"Error processing text: {e}")
            return []


def parse_process_response(content: str) -> List[Dict]:
    """
    Parse the JSON response from the processing API.
    """
    try:
        # Clean up the response
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```) and last line (```)
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        content = content.strip()

        parsed = json.loads(content)

        if isinstance(parsed, list):
            results = []
            seen = set()
            for item in parsed:
                if not isinstance(item, dict):
                    continue

                tibetan = item.get("tibetan", "")
                if not tibetan or tibetan in seen:
                    continue
                seen.add(tibetan)

                results.append({
                    "tibetan": tibetan,
                    "phonetic": item.get("phonetic"),
                    "chinese": item.get("chinese"),
                    "english": item.get("english"),
                    "order": item.get("order", len(results))
                })

            # Sort by order
            results.sort(key=lambda x: x.get("order", 0))
            return results

        return []

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Content: {content[:500]}")
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
    Extract Tibetan phrases - now returns empty list since we use combined processing.
    Kept for compatibility.
    """
    return []


def get_title_from_text(text: str, max_words: int = 5) -> str:
    """
    Generate a title from the first few phrases of Tibetan text.
    Uses simple extraction for title generation.
    """
    words = fallback_extract(text)
    title_words = [w for _, w in words[:max_words]]
    return '་'.join(title_words) if title_words else "无标题"
