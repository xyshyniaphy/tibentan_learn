import json
import httpx
from typing import List, Dict
from app.config import get_settings

settings = get_settings()

PROCESS_PROMPT = """Analyze this Tibetan text and extract meaningful phrases with translations.

Rules:
- Group syllables that form semantic units together (compound words, names, phrases)
- Do NOT split on tsheg (་) - keep meaningful phrases together
- Example: ཨོ་རྒྱན should be ONE phrase, not split into ཨོ and རྒྱན
- Example: བསྐུར་བྱིན་བརླབས should be ONE phrase meaning "blessed/empowered"

Return ONLY a valid JSON array with NO markdown formatting:
[{"tibetan": "phrase", "phonetic": "romanization", "chinese": "中文翻译", "english": "translation", "order": 0}]

Tibetan text:
{text}"""


async def process_tibetan_text_async(text: str) -> List[Dict]:
    """
    Use AI to segment and translate Tibetan text.
    AI decides all phrase boundaries - no Python splitting.
    """
    text = text.strip()

    if not text:
        return []

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


def get_title_from_text(text: str, max_phrases: int = 3) -> str:
    """
    Generate a title from Tibetan text.
    Uses first part of the text directly.
    """
    text = text.strip()
    if not text:
        return "无标题"

    # Just use first ~30 characters of the original text as title
    # Let it be natural without splitting
    if len(text) > 30:
        return text[:30] + "..."
    return text
