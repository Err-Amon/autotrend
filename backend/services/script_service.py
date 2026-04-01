import os
from integrations.gemini_client import gemini_chat
from config import SCRIPTS_DIR
from utils.logger import get_logger

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

    script = gemini_chat(messages, max_tokens=5000)

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
