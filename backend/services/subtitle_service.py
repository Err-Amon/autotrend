import os
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_subtitles(script: str, audio_duration: float, job_id: str) -> str | None:
    try:
        sentences = [s.strip() for s in script.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return None

        srt_path = os.path.join(SUBTITLES_DIR, f"{job_id}_subtitles.srt")
        duration_per = audio_duration / len(sentences)

        with open(srt_path, "w") as f:
            for i, sentence in enumerate(sentences):
                start = i * duration_per
                end = start + duration_per
                f.write(f"{i + 1}\n")
                f.write(f"{_fmt_time(start)} --> {_fmt_time(end)}\n")
                f.write(f"{sentence}.\n\n")

        logger.info(f"Subtitles saved: {srt_path}")
        return srt_path
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        return None

def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - math.floor(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
