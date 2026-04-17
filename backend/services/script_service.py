import os
from utils.logger import get_logger
from integrations.openrouter_client import openrouter_chat
from utils.keyword_extractor import extract_keywords_with_openrouter
from config import SCRIPTS_DIR

logger = get_logger(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/qwen-3.6-plus")


def call_openrouter(
    model: str, messages: list[dict], max_tokens: int = 1024
) -> str | None:
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set")
        return None

    import requests

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        logger.info(f"OpenRouter response: {data}")

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


def generate_script(
    topic: str,
    niche: str,
    job_id: str,
    scripts_dir: str = "",
) -> str | None:
    if not topic or not niche:
        logger.error("Topic and niche are required for script generation")
        return None

    messages = [
        {
            "role": "user",
            "content": (
                f"Write a short-form vertical video script (YouTube Shorts / Instagram Reels style) that feels fresh, "
                f"original, and scroll-stopping every time.\n\n"
                f"Topic: {topic}\n"
                f"Niche: {niche}\n\n"
                f"Strict rules:\n"
                f"- Begin with a hook that grabs attention in 3 seconds\n"
                f"- Use short, punchy sentences of max 10 words each\n"
                f"- Keep narration text ONLY — no stage directions, no scene labels, no [brackets]\n"
                f"- Include natural rhythm and pacing to engage viewers\n"
                f"- Use vivid, relatable examples or metaphors when possible\n"
                f"- Total length: 100 to 120 words\n"
                f"- Tone: engaging, confident, fast-paced, and energetic\n"
                f"- Add subtle variation in phrasing each time to make scripts unique\n\n"
                f"Output ONLY the script text — nothing else, no explanations, no extra formatting."
            ),
        }
    ]

    script = None
    # Try OpenRouter Qwen 3.6 Plus first
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_api_key_here":
        script = openrouter_chat(messages, max_tokens=5000)
        if script and len(script.split()) >= 30:
            logger.info(f"[{job_id}] Script generated with OpenRouter")
            return script

    logger.warning(f"[{job_id}] OpenRouter script may need enhancement or failed")

    # Fallback to keyword extraction with OpenRouter if script is not satisfactory
    if not script or len(script.split()) < 30:
        logger.warning(f"[{job_id}] Primary script generation may need enhancement")
        # Extract keywords with OpenRouter to enhance script
        keywords = extract_keywords_with_openrouter(
            script or " ".join([msg["content"] for msg in messages]), max_keywords=10
        )
        if keywords:
            keyword_str = ", ".join(keywords)
            enhancement_messages = [
                {
                    "role": "user",
                    "content": (
                        f"Enhance this script by incorporating these visual keywords: {keyword_str}. "
                        f"Maintain the same format and rules as before."
                    ),
                }
            ]
            enhanced_script = openrouter_chat(enhancement_messages, max_tokens=5000)
            if enhanced_script and len(enhanced_script.split()) >= 30:
                script = enhanced_script
                logger.info(f"[{job_id}] Script enhanced with OpenRouter keywords")

    if not script:
        logger.error(f"[{job_id}] Script generation returned empty")
        return None

    script = script.strip()
    word_count = len(script.split())
    if word_count < 30:
        logger.warning(f"[{job_id}] Script is short ({word_count} words)")

    # Save to per-job scripts directory
    save_dir = scripts_dir or SCRIPTS_DIR
    os.makedirs(save_dir, exist_ok=True)
    script_path = os.path.join(save_dir, "script.txt")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        logger.info(f"[{job_id}] Script saved: {script_path} ({word_count} words)")
    except Exception as e:
        logger.warning(f"[{job_id}] Could not save script: {e}")

    return script
