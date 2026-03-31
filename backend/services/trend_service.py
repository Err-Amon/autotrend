from integrations.news_rss_client import get_news_trends
from integrations.social_trends_client import get_social_trends
from integrations.google_trends_client import get_google_trends
from utils.logger import get_logger

logger = get_logger(__name__)

# Google Trends seed keywords per niche
NICHE_KEYWORDS: dict[str, list[str]] = {
    "Islamic History": ["islamic history", "muslim civilization", "ottoman empire"],
    "Technology": ["artificial intelligence", "technology trends", "tech innovation"],
    "Motivation": ["motivation", "self improvement", "success mindset"],
    "Animals": ["wildlife", "animals nature", "endangered species"],
    "Finance": ["personal finance", "investing tips", "stock market"],
    "Space & Science": ["space exploration", "science discovery", "NASA"],
}


def collect_trends(niche: str) -> list[str]:
    keywords = NICHE_KEYWORDS.get(niche, [niche])

    logger.info(f"Collecting trends for niche: '{niche}'")

    # Source 1: Google News RSS — niche-targeted headlines
    # Free, no key, no approval. Updated continuously.
    news_trends = get_news_trends(niche, limit=15)
    # Source 2: Social media trends — YouTube trending videos + HackerNews top stories
    social_trends = get_social_trends(niche, limit=10)

    # Source 3: Google Trends — search volume data
    google_trends = get_google_trends(keywords)

    all_trends = news_trends + social_trends + google_trends

    # Deduplicate while preserving order, filter very short strings
    seen = set()
    unique = []
    for t in all_trends:
        normalized = t.strip().lower()
        if normalized not in seen and len(t.strip()) > 8:
            seen.add(normalized)
            unique.append(t.strip())

    logger.info(
        f"Trends collected — "
        f"News RSS: {len(news_trends)}, "
        f"Social (YT+HN): {len(social_trends)}, "
        f"Google Trends: {len(google_trends)}, "
        f"Total unique: {len(unique)}"
    )

    if not unique:
        logger.warning(f"No trends collected for '{niche}' — check network connection")

    return unique[:25]
