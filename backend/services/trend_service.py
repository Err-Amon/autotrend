from integrations.reddit_client import get_reddit_trends
from integrations.twitter_scraper import get_twitter_trends
from integrations.google_trends_client import get_google_trends
from utils.logger import get_logger

logger = get_logger(__name__)

NICHE_SUBREDDITS: dict[str, list[str]] = {
    "Islamic History": ["history", "islam", "MuslimHistory", "AskHistorians"],
    "Technology": ["technology", "tech", "artificial", "MachineLearning"],
    "Motivation": [
        "getmotivated",
        "selfimprovement",
        "productivity",
        "DecidingToBeBetter",
    ],
    "Animals": ["aww", "animals", "NatureIsFuckingLit", "wildlifephotography"],
    "Finance": ["personalfinance", "investing", "financialindependence", "stocks"],
    "Space & Science": ["space", "science", "Astronomy", "Physics"],
}

NICHE_KEYWORDS: dict[str, list[str]] = {
    "Islamic History": ["islamic history", "muslim civilization", "ottoman empire"],
    "Technology": ["artificial intelligence", "technology trends"],
    "Motivation": ["motivation", "self improvement", "success mindset"],
    "Animals": ["wildlife", "animals nature"],
    "Finance": ["personal finance", "investing tips"],
    "Space & Science": ["space exploration", "science discovery"],
}


def collect_trends(niche: str) -> list[str]:
    subreddits = NICHE_SUBREDDITS.get(niche, ["popular"])
    keywords = NICHE_KEYWORDS.get(niche, [niche])

    logger.info(f"Collecting trends for niche: {niche}")

    reddit_trends = get_reddit_trends(subreddits, limit=10)
    twitter_trends = get_twitter_trends(niche, limit=8)
    google_trends = get_google_trends(keywords)

    all_trends = reddit_trends + twitter_trends + google_trends

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in all_trends:
        normalized = t.strip().lower()
        if normalized not in seen and len(t.strip()) > 5:
            seen.add(normalized)
            unique.append(t.strip())

    logger.info(
        f"Trends collected — Reddit: {len(reddit_trends)}, "
        f"Twitter: {len(twitter_trends)}, "
        f"Google: {len(google_trends)}, "
        f"Total unique: {len(unique)}"
    )

    return unique[:25]
