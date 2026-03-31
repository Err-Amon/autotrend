import os
from integrations.groq_client import groq_chat
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
                f"Write a short-form vertical video script (YouTube Shorts / Instagram Reels style).\n\n"
                f"Topic: {topic}\n"
                f"Niche: {niche}\n\n"
                f"Strict rules:\n"
                f"- First sentence must be a powerful hook that stops the scroll\n"
                f"- Use short, punchy sentences of max 10 words each\n"
                f"- Write narration text ONLY — no stage directions, no scene labels, no [brackets]\n"
                f"- End with a clear call to action (follow, like, share)\n"
                f"- Total length: 80 to 120 words\n"
                f"- Tone: engaging, confident, fast-paced\n\n"
                f"Output the script text only. Nothing else."
            ),
        }
    ]

    script = groq_chat(messages, max_tokens=350)

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
