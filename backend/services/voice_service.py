import os
import subprocess
import shutil
import requests
from config import (
    AUDIO_DIR,
    PIPER_EXECUTABLE,
    PIPER_MODEL_PATH,
    USE_TOPMEDIAAI,
    TOPMEDIAAI_API_KEY,
    TOPMEDIAAI_VOICE,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_voice(script: str, job_id: str, audio_dir: str = "") -> str | None:
    if not script or not script.strip():
        logger.error(f"[{job_id}] Cannot generate voice from empty script")
        return None

    save_dir = audio_dir or AUDIO_DIR
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, "audio.mp3")

    if USE_TOPMEDIAAI and TOPMEDIAAI_API_KEY:
        try:
            logger.info(f"[{job_id}] Using TopMediaAI TTS")

            response = requests.post(
                "https://api.topmediaai.com/v1/tts",
                headers={
                    "Authorization": f"Bearer {TOPMEDIAAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"voice": TOPMEDIAAI_VOICE, "text": script, "format": "mp3"},
                timeout=60,
            )

            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)

                # Validate audio file is readable with ffprobe
                try:
                    probe = subprocess.run(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-show_entries",
                            "format=duration",
                            "-of",
                            "default=noprint_wrappers=1:nokey=1",
                            output_path,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if probe.returncode != 0 or not probe.stdout.strip():
                        logger.error(
                            f"[{job_id}] TopMediaAI audio is invalid or corrupt: {probe.stderr}"
                        )
                        os.remove(output_path)
                        raise RuntimeError("TopMediaAI returned invalid MP3")
                except Exception as e:
                    logger.warning(
                        f"[{job_id}] TopMediaAI audio validation failed: {e}"
                    )
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    raise

                logger.info(f"[{job_id}] TopMediaAI voice generated: {output_path}")
                return output_path
            else:
                logger.warning(
                    f"[{job_id}] TopMediaAI failed: {response.status_code} {response.text}"
                )

        except Exception as e:
            logger.warning(f"[{job_id}] TopMediaAI error: {e}")

    logger.info(f"[{job_id}] Falling back to Piper TTS")

    if not shutil.which(PIPER_EXECUTABLE):
        logger.error(f"[{job_id}] Piper not found: {PIPER_EXECUTABLE}")
        return None

    if not os.path.exists(PIPER_MODEL_PATH):
        logger.error(f"[{job_id}] Piper model not found: {PIPER_MODEL_PATH}")
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
            logger.error(f"[{job_id}] Piper failed: {stderr}")
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error(f"[{job_id}] Piper produced empty output")
            return None

        # Validate audio file is readable with ffprobe
        try:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    output_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if probe.returncode != 0 or not probe.stdout.strip():
                logger.error(
                    f"[{job_id}] Audio file is invalid or corrupt: {probe.stderr}"
                )
                os.remove(output_path)
                return None
        except Exception as e:
            logger.warning(f"[{job_id}] Could not validate audio: {e}")

        logger.info(f"[{job_id}] Piper voice generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"[{job_id}] Piper error: {e}")
        return None
