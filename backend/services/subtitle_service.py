import os
import re
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_WORDS_PER_SEGMENT = 8


def generate_subtitles(
    script: str,
    audio_duration: float,
    job_id: str,
    subtitles_dir: str = "",
) -> str | None:
    if not script or not script.strip():
        logger.error(f"[{job_id}] Cannot generate subtitles from empty script")
        return None

    if audio_duration <= 0:
        logger.warning(f"[{job_id}] Invalid audio duration, defaulting to 30s")
        audio_duration = 30.0

    try:
        segments = _split_into_segments(script)
        if not segments:
            logger.error(f"[{job_id}] No subtitle segments produced")
            return None

        save_dir = subtitles_dir or SUBTITLES_DIR
        os.makedirs(save_dir, exist_ok=True)
        srt_path = os.path.join(save_dir, "subtitles.srt")

        total_words = sum(wc for _, wc in segments)
        if total_words == 0:
            logger.warning(
                f"[{job_id}] No words in segments, falling back to equal timing"
            )
            duration_per_segment = audio_duration / len(segments)
            cumulative_time = 0.0
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, (segment, _) in enumerate(segments):
                    start = cumulative_time
                    end = start + duration_per_segment
                    if i == len(segments) - 1:
                        end = audio_duration
                    f.write(f"{i + 1}\n")
                    f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
                    f.write(f"{segment}\n\n")
                    cumulative_time = end
        else:
            cumulative_time = 0.0
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, (segment, wc) in enumerate(segments):
                    time_allocated = (wc / total_words) * audio_duration
                    start = cumulative_time
                    end = start + time_allocated
                    if i == len(segments) - 1:
                        end = audio_duration
                    f.write(f"{i + 1}\n")
                    f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
                    f.write(f"{segment}\n\n")
                    cumulative_time = end

        logger.info(
            f"[{job_id}] Subtitles saved: {srt_path} ({len(segments)} segments)"
        )
        return srt_path

    except Exception as e:
        logger.error(f"[{job_id}] Subtitle generation failed: {e}")
        return None


def _split_into_segments(text: str) -> list[tuple[str, int]]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        if len(words) > MAX_WORDS_PER_SEGMENT:
            for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
                chunk = " ".join(words[i : i + MAX_WORDS_PER_SEGMENT])
                segments.append((chunk, len(chunk.split())))
        else:
            segments.append((sentence, len(words)))
    return segments


def _format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - math.floor(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
