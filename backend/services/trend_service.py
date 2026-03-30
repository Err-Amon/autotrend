from integrations.news_rss_client import get_news_trends
from integrations.twitter_scraper import get_twitter_trends
from integrations.google_trends_client import get_google_trends
from utils.logger import get_logger

logger = get_logger(__name__)

# Google Trends keywords per niche
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

    # Source 1: Google News RSS — niche-targeted headlines, no key needed
    news_trends = get_news_trends(niche, limit=15)

    # Source 2: Twitter/Nitter RSS — real-time social trending, no key needed
    twitter_trends = get_twitter_trends(niche, limit=8)

    # Source 3: Google Trends — search volume trending queries
    google_trends = get_google_trends(keywords)

    all_trends = news_trends + twitter_trends + google_trends

    # Deduplicate while preserving order, filter out very short strings
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
        f"Twitter/Nitter: {len(twitter_trends)}, "
        f"Google Trends: {len(google_trends)}, "
        f"Total unique: {len(unique)}"
    )

    if not unique:
        logger.warning(
            f"No trends collected for '{niche}' — all sources returned empty"
        )

    return unique[:25]
