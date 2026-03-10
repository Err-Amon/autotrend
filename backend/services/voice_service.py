import os
import subprocess
from config import AUDIO_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

PIPER_MODEL = "en_US-lessac-medium"

def generate_voice(script: str, job_id: str) -> str | None:
    output_path = os.path.join(AUDIO_DIR, f"{job_id}_audio.wav")
    try:
        result = subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", output_path],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.error(f"Piper TTS failed: {result.stderr.decode()}")
            return None
        logger.info(f"Audio generated: {output_path}")
        return output_path
    except FileNotFoundError:
        logger.error("Piper TTS not installed. Install from https://github.com/rhasspy/piper")
        return None
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return None
