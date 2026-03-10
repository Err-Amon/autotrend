from integrations.reddit_client import get_reddit_trends
from integrations.twitter_scraper import get_twitter_trends
from integrations.google_trends_client import get_google_trends
from utils.logger import get_logger

logger = get_logger(__name__)

NICHE_SUBREDDITS = {
    "Islamic History": ["history", "islam", "MuslimHistory"],
    "Technology": ["technology", "tech", "programming"],
    "Motivation": ["getmotivated", "selfimprovement", "productivity"],
    "Animals": ["aww", "animals", "NatureIsFuckingLit"],
    "Finance": ["personalfinance", "investing", "financialindependence"],
    "Space & Science": ["space", "science", "Astronomy"],
}

NICHE_KEYWORDS = {
    "Islamic History": ["islamic history", "muslim civilization"],
    "Technology": ["technology", "AI"],
    "Motivation": ["motivation", "success"],
    "Animals": ["animals", "wildlife"],
    "Finance": ["finance", "investing"],
    "Space & Science": ["space", "science"],
}

def collect_trends(niche: str) -> list[str]:
    subreddits = NICHE_SUBREDDITS.get(niche, ["popular"])
    keywords = NICHE_KEYWORDS.get(niche, [niche])

    reddit_trends = get_reddit_trends(subreddits, limit=10)
    twitter_trends = get_twitter_trends(niche, limit=5)
    google_trends = get_google_trends(keywords)

    all_trends = reddit_trends + twitter_trends + google_trends
    unique = list(dict.fromkeys(all_trends))
    logger.info(f"Collected {len(unique)} trends for niche: {niche}")
    return unique[:20]
