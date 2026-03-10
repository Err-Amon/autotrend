from utils.keyword_extractor import extract_keywords
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from utils.logger import get_logger

logger = get_logger(__name__)

def fetch_clips_for_script(script: str, job_id: str) -> list[str]:
    keywords = extract_keywords(script, max_keywords=3)
    if not keywords:
        logger.warning("No keywords extracted, using fallback")
        keywords = ["nature"]

    query = " ".join(keywords[:2])
    logger.info(f"Fetching clips for query: {query}")

    clips = fetch_pexels_clips(query, job_id, count=3)
    if len(clips) < 3:
        extra = fetch_pixabay_clips(query, job_id, count=3 - len(clips))
        clips.extend(extra)

    logger.info(f"Fetched {len(clips)} clips")
    return clips
