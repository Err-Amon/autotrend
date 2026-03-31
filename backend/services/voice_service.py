import os
import subprocess
import shutil
from config import AUDIO_DIR, PIPER_EXECUTABLE, PIPER_MODEL_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_voice(
    script: str,
    job_id: str,
    audio_dir: str = "",
) -> str | None:
    if not script or not script.strip():
        logger.error(f"[{job_id}] Cannot generate voice from empty script")
        return None

    save_dir = audio_dir or AUDIO_DIR
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, "audio.wav")

    if not shutil.which(PIPER_EXECUTABLE):
        logger.error(
            f"[{job_id}] Piper TTS '{PIPER_EXECUTABLE}' not found in PATH. "
            f"Download from: https://github.com/rhasspy/piper/releases"
        )
        return None

    if not os.path.exists(PIPER_MODEL_PATH):
        logger.error(
            f"[{job_id}] Piper model not found: {PIPER_MODEL_PATH}. "
            f"Download from: https://huggingface.co/rhasspy/piper-voices"
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
            logger.error(
                f"[{job_id}] Piper failed (exit {result.returncode}): {stderr}"
            )
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error(f"[{job_id}] Piper produced empty output")
            return None

        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"[{job_id}] Voice generated: {output_path} ({size_kb:.1f}KB)")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error(f"[{job_id}] Piper TTS timed out after 120s")
        return None
    except Exception as e:
        logger.error(f"[{job_id}] Voice generation failed: {e}")
        return None
