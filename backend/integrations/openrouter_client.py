import requests
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def openrouter_chat(messages: list[dict], max_tokens: int = 1024) -> str | None:
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set")
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [])
        if not choices:
            logger.error("OpenRouter API returned no choices")
            return None

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            logger.error("OpenRouter API returned no content")
            return None

        logger.info(f"OpenRouter response received ({len(content)} chars)")
        return content.strip()

    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"OpenRouter API HTTP error {e.response.status_code}: {e.response.text}"
        )
        return None
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {e}")
        return None
