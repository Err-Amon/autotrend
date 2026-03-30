import os
from integrations.groq_client import groq_chat
from config import SCRIPTS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_script(topic: str, niche: str, job_id: str) -> str | None:
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
        logger.error(f"Script generation returned empty for job {job_id}")
        return None

    script = script.strip()

    # Basic validation
    word_count = len(script.split())
    if word_count < 30:
        logger.warning(f"Script seems too short ({word_count} words) for job {job_id}")

    # Save to disk
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    script_path = os.path.join(SCRIPTS_DIR, f"{job_id}_script.txt")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        logger.info(f"Script saved: {script_path} ({word_count} words)")
    except Exception as e:
        logger.warning(f"Could not save script to disk: {e}")

    return script
