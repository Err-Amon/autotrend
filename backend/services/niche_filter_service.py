import json
import os
from utils.logger import get_logger
from integrations.openrouter_client import openrouter_chat

logger = get_logger(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


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
                f"You are a content strategist specializing in short-form viral video.\n\n"
                f"Given these trending topics:\n{trends_text}\n\n"
                f"Your task:\n"
                f"1. Select or adapt the 3 most compelling, attention-grabbing ideas for the niche: '{niche}'\n"
                f"2. Each idea must be a genuine news event, discovery, fact, or interesting story — "
                f"something that would make a viewer stop scrolling\n"
                f"3. Each idea must be specific enough to write a 30-60 second video script about\n"
                f"4. Adapt general trends to fit the niche if needed\n\n"
                f"STRICT RULES — you MUST follow these:\n"
                f"- REJECT any topic that is an advertisement, promotion, sponsored content, "
                f"product sale, course, webinar, affiliate offer, or anything trying to sell something\n"
                f"- REJECT vague clickbait with no real substance\n"
                f"- ONLY pick real events, breaking news, scientific discoveries, historical facts, "
                f"surprising statistics, or genuinely interesting stories\n"
                f"- If no suitable topic exists in the list, create a compelling topic idea "
                f"relevant to the niche '{niche}' based on current trends\n\n"
                f"Return ONLY a valid JSON array of exactly 3 short topic strings. "
                f"No explanation, no markdown, no extra text.\n"
                f'Example: ["Topic one", "Topic two", "Topic three"]'
            ),
        }
    ]

    # Use OpenRouter Qwen 3.6 Plus instead of Gemini
    response = openrouter_chat(messages, max_tokens=200)

    if not response:
        logger.warning(
            "OpenRouter returned no response for trend filtering, using raw trends"
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
