import os
import re
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_CHARS_PER_LINE = 40
MAX_WORDS_PER_SEGMENT = 8


def generate_subtitles(script: str, audio_duration: float, job_id: str) -> str | None:
    if not script or not script.strip():
        logger.error("Cannot generate subtitles from empty script")
        return None

    if audio_duration <= 0:
        logger.warning(f"Invalid audio duration ({audio_duration}), defaulting to 30s")
        audio_duration = 30.0

    try:
        segments = _split_into_segments(script)
        if not segments:
            logger.error("No segments produced from script")
            return None

        os.makedirs(SUBTITLES_DIR, exist_ok=True)
        srt_path = os.path.join(SUBTITLES_DIR, f"{job_id}_subtitles.srt")

        duration_per_segment = audio_duration / len(segments)

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                start = i * duration_per_segment
                end = start + duration_per_segment
                f.write(f"{i + 1}\n")
                f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
                f.write(f"{segment}\n\n")

        logger.info(f"Subtitles saved: {srt_path} ({len(segments)} segments)")
        return srt_path

    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        return None


def _split_into_segments(text: str) -> list[str]:
    # Split on sentence boundaries first
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()

        # Break long sentences into smaller subtitle segments
        if len(words) > MAX_WORDS_PER_SEGMENT:
            for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
                chunk = " ".join(words[i : i + MAX_WORDS_PER_SEGMENT])
                segments.append(chunk)
        else:
            segments.append(sentence)

    return segments


def _format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - math.floor(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
