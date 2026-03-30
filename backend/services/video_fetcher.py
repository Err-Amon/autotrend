from utils.keyword_extractor import extract_keywords, keywords_to_query
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CLIPS = 2
TARGET_CLIPS = 4


def fetch_clips_for_script(script: str, job_id: str) -> list[str]:
    keywords = extract_keywords(script, max_keywords=5)

    if not keywords:
        logger.warning(
            "No keywords extracted from script, using fallback query 'nature'"
        )
        keywords = ["nature"]

    # Use top 2-3 keywords as search query
    query = keywords_to_query(keywords, max_words=3)
    logger.info(f"Fetching clips for query: '{query}'")

    clips: list[str] = []

    # Try Pexels first (higher quality portrait videos)
    pexels_clips = fetch_pexels_clips(query, job_id, count=TARGET_CLIPS)
    clips.extend(pexels_clips)

    # Fill remaining from Pixabay if needed
    remaining = TARGET_CLIPS - len(clips)
    if remaining > 0:
        logger.info(
            f"Pexels returned {len(pexels_clips)} clips, fetching {remaining} more from Pixabay"
        )
        pixabay_clips = fetch_pixabay_clips(query, job_id, count=remaining)
        clips.extend(pixabay_clips)

    # If still not enough, try a broader single-keyword query
    if len(clips) < MIN_CLIPS and len(keywords) > 1:
        fallback_query = keywords[0]
        logger.warning(
            f"Only {len(clips)} clips found for '{query}', "
            f"trying broader query: '{fallback_query}'"
        )
        extra = fetch_pexels_clips(fallback_query, f"{job_id}_fb", count=MIN_CLIPS)
        clips.extend(extra)

    if not clips:
        logger.error(f"No clips fetched for job {job_id}")
    else:
        logger.info(f"Total clips fetched for job {job_id}: {len(clips)}")

    return clips
