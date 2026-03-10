import os
from integrations.groq_client import groq_chat
from config import SCRIPTS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_script(topic: str, niche: str, job_id: str) -> str | None:
    messages = [
        {
            "role": "user",
            "content": (
                f"Write a 30-60 second vertical short-form video script about: '{topic}' for the niche '{niche}'.\n"
                f"Rules:\n"
                f"- Start with a powerful hook in the first sentence\n"
                f"- Use short, punchy sentences\n"
                f"- No stage directions, no scene labels, narration text only\n"
                f"- End with a call to action\n"
                f"- Maximum 120 words"
            ),
        }
    ]

    script = groq_chat(messages, max_tokens=300)
    if not script:
        logger.error(f"Script generation failed for job {job_id}")
        return None

    path = os.path.join(SCRIPTS_DIR, f"{job_id}_script.txt")
    with open(path, "w") as f:
        f.write(script)

    logger.info(f"Script saved: {path}")
    return script
