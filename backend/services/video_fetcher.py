from utils.keyword_extractor import extract_keywords_with_groq, keywords_to_query
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CLIPS = 2
TARGET_CLIPS = 4


def fetch_clips_for_script(script: str, clips_dir: str, job_id: str) -> list[str]:
    keywords = extract_keywords_with_groq(script, max_keywords=5)

    if not keywords:
        logger.warning(f"[{job_id}] No keywords extracted, using fallback: 'nature'")
        keywords = ["nature"]

    query = keywords_to_query(keywords, max_words=3)
    logger.info(f"[{job_id}] Fetching clips for query: '{query}'")

    clips: list[str] = []

    # Try Pexels first
    pexels_clips = fetch_pexels_clips(query, clips_dir, job_id, count=TARGET_CLIPS)
    clips.extend(pexels_clips)

    # Fill remaining slots from Pixabay
    remaining = TARGET_CLIPS - len(clips)
    if remaining > 0:
        logger.info(
            f"[{job_id}] Pexels gave {len(pexels_clips)}, fetching {remaining} from Pixabay"
        )
        pixabay_clips = fetch_pixabay_clips(query, clips_dir, job_id, count=remaining)
        clips.extend(pixabay_clips)

    # Retry with single broader keyword if still not enough
    if len(clips) < MIN_CLIPS and len(keywords) > 1:
        fallback_query = keywords[0]
        logger.warning(
            f"[{job_id}] Only {len(clips)} clips for '{query}', "
            f"retrying with broader query: '{fallback_query}'"
        )
        extra = fetch_pexels_clips(fallback_query, clips_dir, job_id, count=MIN_CLIPS)
        clips.extend(extra)

    if not clips:
        logger.error(f"[{job_id}] No clips fetched")
    else:
        logger.info(f"[{job_id}] Total clips fetched: {len(clips)}")

    return clips
