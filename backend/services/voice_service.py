import os
import subprocess
import shutil
from config import AUDIO_DIR, PIPER_EXECUTABLE, PIPER_MODEL_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_voice(script: str, job_id: str) -> str | None:
    if not script or not script.strip():
        logger.error("Cannot generate voice from empty script")
        return None

    os.makedirs(AUDIO_DIR, exist_ok=True)
    output_path = os.path.join(AUDIO_DIR, f"{job_id}_audio.wav")

    # Check Piper is installed
    if not shutil.which(PIPER_EXECUTABLE):
        logger.error(
            f"Piper TTS executable '{PIPER_EXECUTABLE}' not found in PATH. "
            f"Install it from: https://github.com/rhasspy/piper/releases"
        )
        return None

    # Check model file exists
    if not os.path.exists(PIPER_MODEL_PATH):
        logger.error(
            f"Piper model not found at: {PIPER_MODEL_PATH}. "
            f"Download the model from: https://huggingface.co/rhasspy/piper-voices"
        )
        return None

    try:
        result = subprocess.run(
            [
                PIPER_EXECUTABLE,
                "--model",
                PIPER_MODEL_PATH,
                "--output_file",
                output_path,
            ],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=120,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            logger.error(f"Piper TTS failed (exit {result.returncode}): {stderr}")
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("Piper produced no output file or empty file")
            return None

        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"Voice generated: {output_path} ({size_kb:.1f}KB)")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error("Piper TTS timed out after 120 seconds")
        return None
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return None
