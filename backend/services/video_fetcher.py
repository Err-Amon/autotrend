import re
from utils.keyword_extractor import extract_keywords_with_groq, get_visual_description
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CLIPS = 2
TARGET_CLIPS = 5  # total clips we aim to collect across all queries

# Generic terms that often lead to irrelevant clips
GENERIC_TERMS = {
    "people",
    "person",
    "man",
    "woman",
    "background",
    "abstract",
    "concept",
    "nature",
    "city",
    "video",
    "footage",
    "clip",
    "stock",
}


def _safe_prefix(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip())[:20]


def _refine_query(query: str) -> str:
    """Refine a search query to be more specific and visual."""
    # Remove generic terms that lead to irrelevant results
    words = query.split()
    refined = [w for w in words if w.lower() not in GENERIC_TERMS]

    # If query becomes too short or empty, return original
    if len(refined) < 1:
        return query

    return " ".join(refined)


def fetch_clips_for_script(script: str, clips_dir: str, job_id: str) -> list[str]:

    keywords = extract_keywords_with_groq(script, max_keywords=5)

    if not keywords:
        logger.warning(f"[{job_id}] No keywords extracted, using fallback: 'nature'")
        keywords = ["nature"]

    # Refine keywords to remove generic terms
    refined_keywords = []
    for kw in keywords:
        refined = _refine_query(kw)
        if refined and refined not in refined_keywords:
            refined_keywords.append(refined)

    if not refined_keywords:
        refined_keywords = keywords

    logger.info(f"[{job_id}] Visual search queries from script: {refined_keywords}")

    clips: list[str] = []
    seen_queries: set[str] = set()

    clips_per_query = max(1, TARGET_CLIPS // len(refined_keywords))

    for idx, query in enumerate(refined_keywords):
        if len(clips) >= TARGET_CLIPS:
            break
        if query in seen_queries:
            continue
        seen_queries.add(query)

        # Unique prefix per query prevents filename collisions in clips_dir
        prefix = f"q{idx}_{_safe_prefix(query)}"

        logger.info(f"[{job_id}] Querying Pexels for: '{query}' (prefix={prefix})")
        pexels = fetch_pexels_clips(
            query,
            clips_dir,
            job_id,
            count=clips_per_query,
            file_prefix=f"pexels_{prefix}",
        )
        clips.extend(pexels)

        # If Pexels didn't fill the slot, try Pixabay for the same query
        if len(pexels) < clips_per_query and len(clips) < TARGET_CLIPS:
            remaining_for_query = clips_per_query - len(pexels)
            logger.info(
                f"[{job_id}] Pexels gave {len(pexels)} for '{query}', "
                f"trying Pixabay for {remaining_for_query} more"
            )
            pixabay = fetch_pixabay_clips(
                query,
                clips_dir,
                job_id,
                count=remaining_for_query,
                file_prefix=f"pixabay_{prefix}",
            )
            clips.extend(pixabay)

    if len(clips) < TARGET_CLIPS and refined_keywords:
        primary_query = refined_keywords[0]
        needed = TARGET_CLIPS - len(clips)
        logger.info(
            f"[{job_id}] Only {len(clips)} clips so far — "
            f"topping up with primary query '{primary_query}' ({needed} more)"
        )
        extra_pexels = fetch_pexels_clips(
            primary_query,
            clips_dir,
            job_id,
            count=needed,
            file_prefix="pexels_topup",
        )
        clips.extend(extra_pexels)

        if len(clips) < TARGET_CLIPS:
            extra_pixabay = fetch_pixabay_clips(
                primary_query,
                clips_dir,
                job_id,
                count=TARGET_CLIPS - len(clips),
                file_prefix="pixabay_topup",
            )
            clips.extend(extra_pixabay)

    if len(clips) < MIN_CLIPS:
        # Use visual description from script as fallback instead of generic 'nature'
        fallback = get_visual_description(script[:200]) if script else "nature"
        logger.warning(
            f"[{job_id}] Still only {len(clips)} clips — "
            f"falling back to visual query: '{fallback}'"
        )
        clips.extend(
            fetch_pexels_clips(
                fallback,
                clips_dir,
                job_id,
                count=MIN_CLIPS,
                file_prefix="pexels_fallback",
            )
        )

    if not clips:
        logger.error(f"[{job_id}] No clips fetched at all")
    else:
        logger.info(f"[{job_id}] Total clips fetched: {len(clips)}")

    return clips
