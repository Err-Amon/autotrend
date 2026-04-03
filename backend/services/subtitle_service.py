import os
import re
import math
from config import SUBTITLES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum words shown on screen at once (2 words for better sync with fast-paced shorts)
MAX_WORDS_PER_SEGMENT = 2

# Gemini TTS actual speech rates - calibrated for precise sync
# Gemini TTS (Aoede voice) speaks at approximately 3.0 words per second for clear speech
BASE_WORDS_PER_SECOND = 3.0

# Short words (1-3 chars) are spoken faster
SHORT_WORD_WPS = 3.6

# Long words (7+ chars) are spoken slower
LONG_WORD_WPS = 2.6

# Minimum time a subtitle card stays on screen (prevents flash-frames)
MIN_SEGMENT_DURATION = 0.6

# Gap between subtitle cards - minimal for tight sync
INTER_SEGMENT_GAP = 0.05

# Padding added to the end of the last segment
TAIL_PADDING = 0.1

# Pause duration for punctuation (commas, periods, etc.) - reduced for tighter sync
PAUSE_DURATION_COMMA = 0.15
PAUSE_DURATION_SENTENCE = 0.3


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
        ass_path = os.path.join(save_dir, "subtitles.ass")

        timings = _compute_timings(segments, audio_duration)

        # Generate SRT format (basic compatibility)
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, ((text, _wc, _pause), (start, end)) in enumerate(
                zip(segments, timings), start=1
            ):
                f.write(f"{i}\n")
                f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
                f.write(f"{text}\n\n")

        # Generate ASS format (advanced styling, no fade effects)
        _generate_ass_file(ass_path, segments, timings)

        logger.info(
            f"[{job_id}] Subtitles saved: {srt_path} (SRT) and {ass_path} (ASS) "
            f"({len(segments)} segments, audio={audio_duration:.2f}s)"
        )
        return srt_path

    except Exception as e:
        logger.error(f"[{job_id}] Subtitle generation failed: {e}")
        return None


def _split_into_segments(text: str) -> list[tuple[str, int, str]]:
    # Remove quotes from text for cleaner subtitles
    text = text.strip().strip('"').strip("'")

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text)
    segments: list[tuple[str, int, str]] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if sentence ends with punctuation for pause type
        ends_with_sentence = bool(re.search(r"[.!?]$", sentence))
        # Remove trailing punctuation for processing
        sentence_clean = re.sub(r"[.!?]+$", "", sentence)

        # Split on commas and conjunctions for natural pauses
        phrases = re.split(r"(?:,|;\s+|; )", sentence_clean)

        for idx, phrase in enumerate(phrases):
            phrase = phrase.strip().strip('"').strip("'")
            if not phrase:
                continue

            # Determine pause type
            is_last_phrase = idx == len(phrases) - 1
            if ends_with_sentence and is_last_phrase:
                pause_type = "sentence"
            elif not is_last_phrase and len(phrases) > 1:
                pause_type = "comma"
            else:
                pause_type = "none"

            words = phrase.split()
            # Chunk into groups of MAX_WORDS_PER_SEGMENT (tighter = better sync)
            for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
                chunk_words = words[i : i + MAX_WORDS_PER_SEGMENT]
                chunk = " ".join(chunk_words)
                # Only add pause to the last chunk of a phrase
                chunk_pause = (
                    pause_type if (i + MAX_WORDS_PER_SEGMENT >= len(words)) else "none"
                )
                segments.append((chunk, len(chunk_words), chunk_pause))

    return segments


def _compute_timings(
    segments: list[tuple[str, int, str]],
    audio_duration: float,
) -> list[tuple[float, float]]:
    """
    Compute subtitle timings with precise synchronization to Gemini TTS audio.
    Uses a direct mapping approach: each segment's display time is proportional
    to its position in the total audio duration.
    """
    n = len(segments)
    if n == 0:
        return []

    # Calculate total "weight" based on word count and pauses
    total_weight = 0
    weights = []

    for text, wc, pause_type in segments:
        # Weight is primarily based on word count
        weight = wc

        # Add small pause weight for punctuation
        if pause_type == "sentence":
            weight += 0.3
        elif pause_type == "comma":
            weight += 0.15

        weights.append(weight)
        total_weight += weight

    # Calculate available time (subtract minimal gaps)
    total_gap = INTER_SEGMENT_GAP * (n - 1)
    available_time = audio_duration - total_gap - TAIL_PADDING

    if available_time < audio_duration * 0.5:
        available_time = audio_duration * 0.8

    # Map each segment to its time slot
    timings = []
    cursor = 0.0

    for i, (weight, (text, wc, pause_type)) in enumerate(zip(weights, segments)):
        # Calculate duration proportionally
        proportion = weight / total_weight
        duration = proportion * available_time

        # Ensure minimum display time
        duration = max(duration, MIN_SEGMENT_DURATION)

        start = round(cursor, 3)
        end = round(start + duration, 3)

        # Last segment ends exactly at audio_duration
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


def _generate_ass_file(
    ass_path: str,
    segments: list[tuple[str, int, str]],
    timings: list[tuple[float, float]],
):
    with open(ass_path, "w", encoding="utf-8") as f:
        # ASS file header
        f.write("[Script Info]\n")
        f.write("Title: Auto-generated Subtitles\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("WrapStyle: 0\n")
        f.write("ScaledBorderAndShadow: yes\n\n")

        # Style definition - optimized for vertical video (1080x1920)
        f.write("[V4+ Styles]\n")
        f.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )
        # Large, bold text for maximum impact - 72px for 1080x1920 vertical video
        f.write(
            "Style: Default,Noto Sans Bold,72,&H00FFFFFF,&H00FFFF00,&H00000000,&H88000000,-1,0,0,0,100,100,3,0,1,4,5,2,60,60,150,1\n\n"
        )

        # Events
        f.write("[Events]\n")
        f.write(
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        for i, ((text, _wc, _pause), (start, end)) in enumerate(
            zip(segments, timings), start=1
        ):
            start_time = _format_time_ass(start)
            end_time = _format_time_ass(end)
            # Simple display - no fade effects
            f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n")


def _format_time_ass(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    c = int(round((seconds - math.floor(seconds)) * 100))
    c = min(c, 99)
    return f"{h}:{m:02}:{s:02}.{c:02}"
