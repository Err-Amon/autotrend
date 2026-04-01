import os
import re
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum words shown on screen at once (3 words for better readability)
MAX_WORDS_PER_SEGMENT = 3

# Gemini TTS actual speech rates - calibrated for sync with readability
# Base rate for medium-length words (4-6 chars)
BASE_WORDS_PER_SECOND = 3.5  # Gemini's actual speed

# Short words (1-3 chars) are spoken faster
SHORT_WORD_WPS = 4.0

# Long words (7+ chars) are spoken slower
LONG_WORD_WPS = 3.0

# Minimum time a subtitle card stays on screen (prevents flash-frames)
MIN_SEGMENT_DURATION = 0.6  # seconds (reduced to sync with fast TTS)

# Gap between subtitle cards - tighter for better sync
INTER_SEGMENT_GAP = 0.01  # seconds

# Padding added to the end of the last segment
TAIL_PADDING = 0.1  # seconds


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
    """
    Split text into segments (2 words each for tight sync with audio).
    Also respects natural speech boundaries (commas, phrase breaks).
    """
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments: list[tuple[str, int]] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Split on commas and conjunctions for natural pauses
        phrases = re.split(r"(?:,|;\s+|; )", sentence)

        for phrase in phrases:
            phrase = phrase.strip()
            if not phrase:
                continue

            words = phrase.split()
            # Chunk into groups of MAX_WORDS_PER_SEGMENT (tighter = better sync)
            for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
                chunk_words = words[i : i + MAX_WORDS_PER_SEGMENT]
                chunk = " ".join(chunk_words)
                segments.append((chunk, len(chunk_words)))

    return segments


def _compute_timings(
    segments: list[tuple[str, int]],
    audio_duration: float,
) -> list[tuple[float, float]]:
    """
    Compute subtitle timings with better synchronization to actual audio duration.
    Uses adaptive scaling to ensure subtitles stay in sync throughout.
    """
    n = len(segments)
    total_gap = INTER_SEGMENT_GAP * (n - 1)
    available = max(audio_duration - total_gap - TAIL_PADDING, audio_duration * 0.5)

    # Step 1: Calculate raw durations with word-complexity-aware timing
    raw = []
    for text, wc in segments:
        words = text.split()
        avg_word_len = sum(len(w) for w in words) / len(words) if words else 4

        # Adjust WPS based on word complexity for more accurate timing
        if avg_word_len <= 3:
            wps = SHORT_WORD_WPS  # Short words spoken faster
        elif avg_word_len >= 7:
            wps = LONG_WORD_WPS  # Long words spoken slower
        else:
            wps = BASE_WORDS_PER_SECOND  # Medium words at base rate

        duration = max(wc / wps, MIN_SEGMENT_DURATION)
        raw.append(duration)

    raw_total = sum(raw)

    # Step 2: Adaptive scaling - ensures perfect fit to audio duration
    if raw_total > 0:
        scale = available / raw_total
    else:
        scale = 1.0

    durations = [max(r * scale, MIN_SEGMENT_DURATION) for r in raw]

    # Step 3: Build timings with precise cursor tracking
    timings: list[tuple[float, float]] = []
    cursor = 0.0
    for i, dur in enumerate(durations):
        start = round(cursor, 3)
        end = round(start + dur, 3)

        # Last segment ends exactly at audio_duration (no overshoot)
        if i == n - 1:
            end = audio_duration

        timings.append((start, end))
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
