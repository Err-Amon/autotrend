import os
import re
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum words shown on screen at once (3-4 words = short-form video style)
MAX_WORDS_PER_SEGMENT = 4

# Gemini TTS speaks at ~3.5-4.0 wps; 3.8 keeps subtitles in sync with the voice
WORDS_PER_SECOND = 3.8

# Minimum time a subtitle card stays on screen (prevents flash-frames)
MIN_SEGMENT_DURATION = 0.5  # seconds

# Gap between subtitle cards so the screen briefly clears between phrases
INTER_SEGMENT_GAP = 0.04  # seconds

# Padding added to the end of the last segment so it doesn't cut off abruptly
TAIL_PADDING = 0.2  # seconds


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

        timings = _compute_timings(segments, audio_duration)

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, ((text, _wc), (start, end)) in enumerate(
                zip(segments, timings), start=1
            ):
                f.write(f"{i}\n")
                f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
                f.write(f"{text}\n\n")

        logger.info(
            f"[{job_id}] Subtitles saved: {srt_path} "
            f"({len(segments)} segments, audio={audio_duration:.2f}s)"
        )
        return srt_path

    except Exception as e:
        logger.error(f"[{job_id}] Subtitle generation failed: {e}")
        return None


def _split_into_segments(text: str) -> list[tuple[str, int]]:

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments: list[tuple[str, int]] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()
        # Chunk the sentence into groups of MAX_WORDS_PER_SEGMENT
        for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
            chunk_words = words[i : i + MAX_WORDS_PER_SEGMENT]
            chunk = " ".join(chunk_words)
            segments.append((chunk, len(chunk_words)))

    return segments


def _compute_timings(
    segments: list[tuple[str, int]],
    audio_duration: float,
) -> list[tuple[float, float]]:

    n = len(segments)
    total_gap = INTER_SEGMENT_GAP * (n - 1)
    available = max(audio_duration - total_gap - TAIL_PADDING, audio_duration * 0.5)

    # Step 1 & 2: raw durations
    raw = [max(wc / WORDS_PER_SECOND, MIN_SEGMENT_DURATION) for _, wc in segments]
    raw_total = sum(raw)

    # Step 3: scale so durations fill available time
    scale = available / raw_total if raw_total > 0 else 1.0
    durations = [r * scale for r in raw]

    # Step 4: build timings
    timings: list[tuple[float, float]] = []
    cursor = 0.0
    for i, dur in enumerate(durations):
        start = cursor
        end = start + dur
        # Last segment ends exactly at audio_duration (no overshoot)
        if i == n - 1:
            end = audio_duration
        timings.append((round(start, 3), round(end, 3)))
        cursor = end + INTER_SEGMENT_GAP

    return timings


def _format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - math.floor(seconds)) * 1000))
    # Clamp ms to [0, 999] to avoid "1000" edge case
    ms = min(ms, 999)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
