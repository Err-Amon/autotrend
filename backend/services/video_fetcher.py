from utils.keyword_extractor import (
    extract_keywords_with_groq,
    keywords_to_query,
    get_visual_description,
)
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from services.subtitle_service import _split_into_segments
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CLIPS = 2
TARGET_CLIPS = 4


def fetch_clips_for_script(script: str, clips_dir: str, job_id: str) -> list[str]:
    segments = _split_into_segments(script)
    if not segments:
        logger.warning(f"[{job_id}] No segments, using fallback")
        return fetch_clips_fallback(clips_dir, job_id)

    # Limit to TARGET_CLIPS segments
    segments = segments[:TARGET_CLIPS]

    clips: list[str] = []

    for segment, _ in segments:
        description = get_visual_description(segment)
        logger.info(
            f"[{job_id}] Fetching clip for segment: '{segment}' -> '{description}'"
        )

        # Try Pexels first
        pexels_clips = fetch_pexels_clips(description, clips_dir, job_id, count=1)
        if pexels_clips:
            clips.extend(pexels_clips)
        else:
            # Try Pixabay
            pixabay_clips = fetch_pixabay_clips(description, clips_dir, job_id, count=1)
            clips.extend(pixabay_clips)

    # If not enough clips, fill with fallback
    if len(clips) < MIN_CLIPS:
        logger.warning(f"[{job_id}] Only {len(clips)} clips, adding fallback")
        fallback_clips = fetch_clips_fallback(clips_dir, job_id)
        clips.extend(fallback_clips[: MIN_CLIPS - len(clips)])

    if not clips:
        logger.error(f"[{job_id}] No clips fetched")
    else:
        logger.info(f"[{job_id}] Total clips fetched: {len(clips)}")

    return clips


def fetch_clips_fallback(clips_dir: str, job_id: str) -> list[str]:
    query = "nature"
    clips = []
    pexels_clips = fetch_pexels_clips(query, clips_dir, job_id, count=TARGET_CLIPS)
    clips.extend(pexels_clips)
    remaining = TARGET_CLIPS - len(clips)
    if remaining > 0:
        pixabay_clips = fetch_pixabay_clips(query, clips_dir, job_id, count=remaining)
        clips.extend(pixabay_clips)
    return clips
