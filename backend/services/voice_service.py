import os
import re
import subprocess
import shutil
import struct
import wave
import io
import base64
import requests
from config import (
    AUDIO_DIR,
    PIPER_EXECUTABLE,
    PIPER_MODEL_PATH,
    USE_GOOGLE_TTS,
    GOOGLE_AI_STUDIO_API_KEY,
    GOOGLE_TTS_VOICE,
    GOOGLE_TTS_MODEL,
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


def _pcm_to_wav(
    pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2
) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def _generate_voice_google_tts(text: str, job_id: str, output_path: str) -> str | None:
    logger.info(
        f"[{job_id}] Using Google AI Studio Gemini TTS (model: {GOOGLE_TTS_MODEL}, voice: {GOOGLE_TTS_VOICE})"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GOOGLE_TTS_MODEL}:generateContent?key={GOOGLE_AI_STUDIO_API_KEY}"
    )

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GOOGLE_TTS_VOICE}}
            },
        },
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
    except requests.exceptions.Timeout:
        logger.warning(f"[{job_id}] Google AI Studio TTS request timed out")
        return None
    except Exception as e:
        logger.warning(f"[{job_id}] Google AI Studio TTS request error: {e}")
        return None

    if response.status_code != 200:
        logger.warning(
            f"[{job_id}] Google AI Studio TTS HTTP {response.status_code}: {response.text[:500]}"
        )
        return None

    try:
        data = response.json()
    except Exception as e:
        logger.warning(f"[{job_id}] Google AI Studio TTS JSON parse error: {e}")
        return None

    # Navigate the Gemini response structure to extract audio data
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning(
                f"[{job_id}] Google AI Studio TTS: no candidates in response"
            )
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            logger.warning(f"[{job_id}] Google AI Studio TTS: no parts in candidate")
            return None

        inline_data = parts[0].get("inlineData", {})
        mime_type = inline_data.get("mimeType", "")
        audio_b64 = inline_data.get("data", "")

        if not audio_b64:
            logger.warning(
                f"[{job_id}] Google AI Studio TTS: no audio data in response. "
                f"Response keys: {list(data.keys())}"
            )
            return None

        audio_bytes = base64.b64decode(audio_b64)

    except Exception as e:
        logger.warning(
            f"[{job_id}] Google AI Studio TTS: failed to extract audio data: {e}"
        )
        return None

    if not audio_bytes or len(audio_bytes) < 512:
        logger.warning(
            f"[{job_id}] Google AI Studio TTS returned suspiciously small payload "
            f"({len(audio_bytes) if audio_bytes else 0} bytes) — discarding"
        )
        return None

    # Gemini TTS returns raw PCM (L16) audio — wrap in WAV container
    # then convert to MP3 via ffmpeg for compatibility
    try:
        # Determine sample rate from mime_type if available (e.g. "audio/L16;rate=24000")
        sample_rate = 24000
        if "rate=" in mime_type:
            try:
                sample_rate = int(mime_type.split("rate=")[1].split(";")[0].strip())
            except (ValueError, IndexError):
                pass

        wav_bytes = _pcm_to_wav(audio_bytes, sample_rate=sample_rate)

        # Convert WAV → MP3 using ffmpeg
        ffmpeg_proc = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "wav",
                "-i",
                "pipe:0",
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                output_path,
            ],
            input=wav_bytes,
            capture_output=True,
            timeout=60,
        )

        if ffmpeg_proc.returncode != 0:
            stderr = ffmpeg_proc.stderr.decode("utf-8", errors="replace")
            logger.error(f"[{job_id}] ffmpeg WAV→MP3 conversion failed: {stderr}")
            return None

    except Exception as e:
        logger.error(f"[{job_id}] Google AI Studio TTS audio conversion error: {e}")
        return None

    # Validate the final MP3
    if not _validate_audio_file(output_path, job_id):
        logger.error(
            f"[{job_id}] Google AI Studio TTS audio failed validation — removing file"
        )
        try:
            os.remove(output_path)
        except OSError:
            pass
        return None

    logger.info(
        f"[{job_id}] Google AI Studio Gemini TTS voice generated: {output_path}"
    )
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

    if USE_GOOGLE_TTS and GOOGLE_AI_STUDIO_API_KEY:
        google_result = _generate_voice_google_tts(
            script_with_pauses, job_id, output_path
        )
        if google_result:
            return google_result
        # Fall through to Piper if Google TTS failed
        logger.warning(
            f"[{job_id}] Google AI Studio TTS failed — falling back to Piper TTS"
        )

    logger.info(f"[{job_id}] Using Piper TTS")

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
