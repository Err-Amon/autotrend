import json
from integrations.groq_client import groq_chat
from utils.logger import get_logger

logger = get_logger(__name__)


def filter_trends_for_niche(trends: list[str], niche: str) -> list[str]:
    if not trends:
        logger.warning("No trends provided to filter")
        return []

    # Limit input to avoid hitting token limits
    trends_sample = trends[:20]
    trends_text = "\n".join(f"- {t}" for t in trends_sample)

    messages = [
        {
            "role": "user",
            "content": (
                f"You are a content strategist specializing in short-form video.\n\n"
                f"Given these trending topics:\n{trends_text}\n\n"
                f"Your task:\n"
                f"1. Select or adapt the 3 most compelling ideas for the niche: '{niche}'\n"
                f"2. Each idea must be specific enough to write a 30-60 second video script about\n"
                f"3. Adapt general trends to fit the niche if needed\n\n"
                f"Return ONLY a valid JSON array of exactly 3 short topic strings. "
                f"No explanation, no markdown, no extra text.\n"
                f'Example: ["Topic one", "Topic two", "Topic three"]'
            ),
        }
    ]

    response = groq_chat(messages, max_tokens=200)

    if not response:
        logger.warning(
            "Groq returned no response for trend filtering, using raw trends"
        )
        return trends_sample[:3]

    try:
        # Strip any accidental markdown fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        filtered = json.loads(cleaned)

        if not isinstance(filtered, list):
            raise ValueError("Response is not a list")

        filtered = [str(t).strip() for t in filtered if str(t).strip()][:3]

        if not filtered:
            raise ValueError("Parsed list is empty")

        logger.info(
            f"Filtered to {len(filtered)} topics for niche '{niche}': {filtered}"
        )
        return filtered

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(
            f"Could not parse filtered trends ({e}), falling back to raw trends"
        )
        return trends_sample[:3]
    except Exception as e:
        logger.error(f"Trend filtering failed unexpectedly: {e}")
        return trends_sample[:3]
