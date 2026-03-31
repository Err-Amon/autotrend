import os
import re
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

# Sentence-ending punctuation characters
_SENTENCE_END = re.compile(r"([.!?])\s+")


def _add_sentence_pauses(text: str) -> str:
    paused = _SENTENCE_END.sub(r"\1\n\n", text.strip())
    return paused


def _validate_audio_file(path: str, job_id: str) -> bool:
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
                path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if probe.returncode != 0 or not probe.stdout.strip():
            logger.error(
                f"[{job_id}] Audio validation failed — ffprobe stderr: {probe.stderr.strip()}"
            )
            return False
        duration = float(probe.stdout.strip())
        if duration <= 0:
            logger.error(f"[{job_id}] Audio has zero duration")
            return False
        return True
    except Exception as e:
        logger.warning(f"[{job_id}] Could not validate audio with ffprobe: {e}")
        # If ffprobe itself is missing, don't block — assume file is OK
        return True


def _generate_voice_topmediaai(text: str, job_id: str, output_path: str) -> str | None:
    logger.info(f"[{job_id}] Using TopMediaAI TTS")

    try:
        response = requests.post(
            "https://api.topmediaai.com/v1/tts",
            headers={
                "Authorization": f"Bearer {TOPMEDIAAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "voice": TOPMEDIAAI_VOICE,
                "text": text,
                "format": "mp3",
            },
            timeout=90,
        )
    except requests.exceptions.Timeout:
        logger.warning(f"[{job_id}] TopMediaAI request timed out")
        return None
    except Exception as e:
        logger.warning(f"[{job_id}] TopMediaAI request error: {e}")
        return None

    if response.status_code != 200:
        logger.warning(
            f"[{job_id}] TopMediaAI HTTP {response.status_code}: {response.text[:300]}"
        )
        return None

    content_type = response.headers.get("Content-Type", "").lower()
    logger.debug(f"[{job_id}] TopMediaAI Content-Type: {content_type}")

    audio_bytes: bytes | None = None

    # Case A: response body IS the audio
    if "audio" in content_type or "octet-stream" in content_type:
        audio_bytes = response.content

    # Case B: response body is JSON — look for a URL to download
    elif "json" in content_type or response.content.lstrip()[:1] == b"{":
        try:
            data = response.json()
            logger.debug(
                f"[{job_id}] TopMediaAI JSON response keys: {list(data.keys())}"
            )
            # Common field names used by various TTS APIs
            audio_url = (
                data.get("audio_url")
                or data.get("url")
                or data.get("audio")
                or data.get("download_url")
                or data.get("file_url")
            )
            if not audio_url:
                logger.warning(
                    f"[{job_id}] TopMediaAI JSON has no audio URL field. "
                    f"Full response: {data}"
                )
                return None

            logger.info(f"[{job_id}] TopMediaAI: downloading audio from {audio_url}")
            dl = requests.get(audio_url, timeout=60)
            if dl.status_code != 200:
                logger.warning(
                    f"[{job_id}] TopMediaAI audio download failed: HTTP {dl.status_code}"
                )
                return None
            audio_bytes = dl.content

        except Exception as e:
            logger.warning(f"[{job_id}] TopMediaAI JSON parse/download error: {e}")
            return None
    else:
        # Unknown content type — try treating as raw audio anyway
        logger.warning(
            f"[{job_id}] TopMediaAI unknown Content-Type '{content_type}', "
            f"attempting to treat as raw audio"
        )
        audio_bytes = response.content

    if not audio_bytes or len(audio_bytes) < 1024:
        logger.warning(
            f"[{job_id}] TopMediaAI returned suspiciously small payload "
            f"({len(audio_bytes) if audio_bytes else 0} bytes) — discarding"
        )
        return None

    # Write to disk
    try:
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
    except Exception as e:
        logger.error(f"[{job_id}] Could not write TopMediaAI audio: {e}")
        return None

    # Validate
    if not _validate_audio_file(output_path, job_id):
        logger.error(f"[{job_id}] TopMediaAI audio failed validation — removing file")
        try:
            os.remove(output_path)
        except OSError:
            pass
        return None

    logger.info(f"[{job_id}] TopMediaAI voice generated: {output_path}")
    return output_path


def generate_voice(script: str, job_id: str, audio_dir: str = "") -> str | None:
    if not script or not script.strip():
        logger.error(f"[{job_id}] Cannot generate voice from empty script")
        return None

    # Pre-process: add inter-sentence pauses so the TTS output sounds natural
    script_with_pauses = _add_sentence_pauses(script)
    logger.debug(f"[{job_id}] Script after pause insertion:\n{script_with_pauses}")

    save_dir = audio_dir or AUDIO_DIR
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, "audio.mp3")

    if USE_TOPMEDIAAI and TOPMEDIAAI_API_KEY:
        topmedia_result = _generate_voice_topmediaai(
            script_with_pauses, job_id, output_path
        )
        if topmedia_result:
            return topmedia_result
        # Fall through to Piper if TopMediaAI failed

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
            input=script_with_pauses.encode("utf-8"),
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

        if not _validate_audio_file(output_path, job_id):
            logger.error(f"[{job_id}] Piper audio failed validation")
            try:
                os.remove(output_path)
            except OSError:
                pass
            return None

        logger.info(f"[{job_id}] Piper voice generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"[{job_id}] Piper error: {e}")
        return None
