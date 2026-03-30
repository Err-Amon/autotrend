import requests
from config import GROQ_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


def groq_chat(messages: list[dict], max_tokens: int = 1024) -> str | None:
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            GROQ_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"Groq response received ({len(content)} chars)")
        return content
    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Groq API HTTP error {e.response.status_code}: {e.response.text}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Groq API unexpected response structure: {e}")
        return None
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return None
