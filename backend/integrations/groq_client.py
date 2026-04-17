import requests
from config import GROQ_API_KEY, GROQ_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def groq_chat(messages: list[dict], max_tokens: int = 1024) -> str | None:
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [])
        if not choices:
            logger.error("Groq API returned no choices")
            return None

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            logger.error("Groq API returned no content")
            return None

        logger.info(f"Groq response received ({len(content)} chars)")
        return content.strip()

    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Groq API HTTP error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return None
