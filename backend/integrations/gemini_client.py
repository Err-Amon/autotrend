import requests
from config import GOOGLE_AI_STUDIO_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
MODEL = "gemini-2.5-flash"


def gemini_chat(messages: list[dict], max_tokens: int = 1024) -> str | None:
    if not GOOGLE_AI_STUDIO_API_KEY:
        logger.error("GOOGLE_AI_STUDIO_API_KEY is not set")
        return None

    # Convert OpenAI-style messages to Gemini format
    contents = []
    system_instruction = ""

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Gemini uses "user" and "model" roles
        if role == "system":
            # Store system messages separately for system_instruction
            system_instruction = content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})

    # Ensure we have at least one message
    if not contents:
        logger.error("No valid messages to send to Gemini")
        return None

    params = {"key": GOOGLE_AI_STUDIO_API_KEY}
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max(
                max_tokens, 4000
            ),  # Ensure minimum 4000 tokens for longer content
            "temperature": 1.0,  # Maximum creativity
            "topP": 0.98,
            "topK": 100,
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_CIVIC_INTEGRITY",
                "threshold": "BLOCK_NONE",
            },
        ],
    }

    # Add system instruction if present
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    try:
        response = requests.post(
            GEMINI_URL,
            json=payload,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        # Extract content from Gemini response
        candidates = data.get("candidates", [])
        if not candidates:
            logger.error("Gemini API returned no candidates")
            logger.debug(f"Full response: {data}")
            return None

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason", "UNKNOWN")

        # Check for safety filters or incomplete responses
        if finish_reason == "SAFETY":
            logger.warning("Gemini: Response blocked by safety filters")
            return None
        if finish_reason == "MAX_TOKENS":
            logger.warning("Gemini: Response cut off due to max tokens limit")

        content_parts = candidate.get("content", {}).get("parts", [])
        if not content_parts:
            logger.error(
                f"Gemini API returned no content parts (finishReason: {finish_reason})"
            )
            logger.debug(f"Full response: {data}")
            return None

        content = content_parts[0].get("text", "").strip()
        content_length = len(content)
        word_count = len(content.split()) if content else 0
        logger.info(
            f"Gemini response received ({content_length} chars, {word_count} words, finishReason: {finish_reason})"
        )

        if word_count < 20:
            logger.warning(
                f"Gemini returned very short response: {word_count} words. Full text: {content[:200]}"
            )

        return content

    except requests.exceptions.Timeout:
        logger.error("Gemini API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        error_msg = f"Gemini API HTTP error {e.response.status_code}"
        try:
            error_body = e.response.json()
            error_msg += f": {error_body}"
        except:
            error_msg += f": {e.response.text[:500]}"
        logger.error(error_msg)
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Gemini API unexpected response structure: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None
