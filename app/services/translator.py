import httpx
import json
import asyncio
from typing import List, Dict, Optional
from app.config import get_settings

settings = get_settings()

PROMPT_TEMPLATE = """Translate these Tibetan phrases/words. Each item may be a single word or a compound phrase. For each phrase provide:
- tibetan: the original Tibetan text (exactly as provided)
- phonetic: simple romanized pronunciation (e.g., "ta-she de-le" for multi-syllable phrases)
- chinese: Chinese translation (can be a phrase or single word)
- english: English translation

Return ONLY a valid JSON array with no markdown formatting:
[{{"tibetan": "phrase", "phonetic": "...", "chinese": "...", "english": "..."}}]

Phrases to translate: {words}"""

BATCH_SIZE = 12
MAX_RETRIES = 3
RETRY_DELAY = 1.0


async def translate_words(words: List[str]) -> List[Dict]:
    """
    Translate a list of Tibetan words using GLM API.
    Batches words and handles retries with exponential backoff.
    """
    results = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(words), BATCH_SIZE):
            batch = words[i:i + BATCH_SIZE]
            batch_results = await translate_batch_with_retry(client, batch)
            results.extend(batch_results)

    return results


async def translate_batch_with_retry(client: httpx.AsyncClient, words: List[str]) -> List[Dict]:
    """
    Translate a batch of words with exponential backoff retry.
    """
    words_str = " ".join(words)
    prompt = PROMPT_TEMPLATE.format(words=words_str)

    for attempt in range(MAX_RETRIES):
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
                        {"role": "user", "content": prompt}
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return parse_translation_response(content, words)
            elif response.status_code == 429:
                # Rate limited - wait and retry
                delay = RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")

        except httpx.RequestError as e:
            if attempt == MAX_RETRIES - 1:
                # Return empty results on final failure
                return [{"tibetan": w, "phonetic": None, "chinese": None, "english": None} for w in words]
            delay = RETRY_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)

    # All retries failed
    return [{"tibetan": w, "phonetic": None, "chinese": None, "english": None} for w in words]


def parse_translation_response(content: str, original_words: List[str]) -> List[Dict]:
    """
    Parse the JSON response from the API.
    """
    try:
        # Clean up the response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]  # Remove first line
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]  # Remove last line
        content = content.strip()

        parsed = json.loads(content)

        if isinstance(parsed, list):
            # Normalize keys - handle different key names
            normalized = []
            for idx, item in enumerate(parsed):
                if not isinstance(item, dict):
                    continue
                # Find the Tibetan word key (could be "tibetan", "tibetan_word", "word", etc.)
                tibetan_value = None
                for key in ["tibetan", "tibetan_word", "word", "tibetanWord", "original"]:
                    if key in item and item[key]:
                        tibetan_value = item[key]
                        break

                if tibetan_value:
                    normalized.append({
                        "tibetan": tibetan_value,
                        "phonetic": item.get("phonetic") or item.get("pronunciation"),
                        "chinese": item.get("chinese") or item.get("zh") or item.get("chinese_translation"),
                        "english": item.get("english") or item.get("en") or item.get("english_translation")
                    })
                elif idx < len(original_words):
                    # If no Tibetan key found, use the original word
                    normalized.append({
                        "tibetan": original_words[idx],
                        "phonetic": item.get("phonetic") or item.get("pronunciation"),
                        "chinese": item.get("chinese") or item.get("zh") or item.get("chinese_translation"),
                        "english": item.get("english") or item.get("en") or item.get("english_translation")
                    })

            # If we couldn't parse any items, fall back to original words
            if not normalized:
                return [{"tibetan": w, "phonetic": None, "chinese": None, "english": None} for w in original_words]

            return normalized
        else:
            raise ValueError("Response is not a list")

    except (json.JSONDecodeError, ValueError):
        # Return empty results if parsing fails
        return [{"tibetan": w, "phonetic": None, "chinese": None, "english": None} for w in original_words]
