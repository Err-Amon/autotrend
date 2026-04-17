import os
from utils.logger import get_logger
from integrations.openrouter_client import openrouter_chat
from integrations.groq_client import groq_chat
from utils.keyword_extractor import extract_keywords_with_openrouter
from config import SCRIPTS_DIR, OPENROUTER_API_KEY, GROQ_API_KEY

logger = get_logger(__name__)


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
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_api_key_here":
        script = openrouter_chat(messages, max_tokens=5000)
        if script and len(script.split()) >= 30:
            logger.info(f"[{job_id}] Script generated with OpenRouter")
            return script
        logger.warning(f"[{job_id}] OpenRouter failed, trying Groq")

    if not script and GROQ_API_KEY:
        script = groq_chat(messages, max_tokens=5000)
        if script and len(script.split()) >= 30:
            logger.info(f"[{job_id}] Script generated with Groq")
            return script
        logger.warning(f"[{job_id}] Groq failed")

    if not script or len(script.split()) < 30:
        logger.warning(f"[{job_id}] Primary script generation may need enhancement")
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
            if not enhanced_script and GROQ_API_KEY:
                enhanced_script = groq_chat(enhancement_messages, max_tokens=5000)
            if enhanced_script and len(enhanced_script.split()) >= 30:
                script = enhanced_script
                logger.info(f"[{job_id}] Script enhanced with keywords")

    if not script:
        logger.error(f"[{job_id}] Script generation returned empty")
        return None

    script = script.strip()
    word_count = len(script.split())
    if word_count < 30:
        logger.warning(f"[{job_id}] Script is short ({word_count} words)")

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
