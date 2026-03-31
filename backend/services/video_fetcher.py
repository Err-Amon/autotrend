import re
from utils.keyword_extractor import extract_keywords_with_groq
from integrations.pexels_client import fetch_pexels_clips
from integrations.pixabay_client import fetch_pixabay_clips
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CLIPS = 2
TARGET_CLIPS = 5  # total clips we aim to collect across all queries


def _safe_prefix(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip())[:20]


def fetch_clips_for_script(script: str, clips_dir: str, job_id: str) -> list[str]:

    keywords = extract_keywords_with_groq(script, max_keywords=5)

    if not keywords:
        logger.warning(f"[{job_id}] No keywords extracted, using fallback: 'nature'")
        keywords = ["nature"]

    logger.info(f"[{job_id}] Visual search queries from script: {keywords}")

    clips: list[str] = []
    seen_queries: set[str] = set()

    clips_per_query = max(1, TARGET_CLIPS // len(keywords))

    for idx, query in enumerate(keywords):
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

    if len(clips) < TARGET_CLIPS and keywords:
        primary_query = keywords[0]
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
        fallback = "nature"
        logger.warning(
            f"[{job_id}] Still only {len(clips)} clips — "
            f"falling back to generic query: '{fallback}'"
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
