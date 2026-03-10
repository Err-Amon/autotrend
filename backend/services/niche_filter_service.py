from integrations.groq_client import groq_chat
from utils.logger import get_logger

logger = get_logger(__name__)

def filter_trends_for_niche(trends: list[str], niche: str) -> list[str]:
    if not trends:
        return []

    trends_text = "\n".join(f"- {t}" for t in trends)
    messages = [
        {
            "role": "user",
            "content": (
                f"You are a content strategist. Given these trending topics:\n{trends_text}\n\n"
                f"Select and adapt the 3 most relevant ideas for the niche: '{niche}'.\n"
                f"Return only a JSON array of 3 short topic strings. No explanation. Example:\n"
                f'["Topic 1", "Topic 2", "Topic 3"]'
            ),
        }
    ]

    response = groq_chat(messages, max_tokens=256)
    if not response:
        return trends[:3]

    try:
        import json
        cleaned = response.strip().strip("```json").strip("```").strip()
        filtered = json.loads(cleaned)
        logger.info(f"Filtered to {len(filtered)} niche topics")
        return filtered if isinstance(filtered, list) else trends[:3]
    except Exception as e:
        logger.warning(f"Could not parse filtered trends: {e}")
        return trends[:3]
