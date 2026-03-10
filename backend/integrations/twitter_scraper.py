from utils.logger import get_logger

logger = get_logger(__name__)

def get_twitter_trends(query: str, limit: int = 10) -> list[str]:
    try:
        import snscrape.modules.twitter as sntwitter
        trends = []
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{query} lang:en").get_items()):
            if i >= limit:
                break
            trends.append(tweet.content)
        return trends
    except Exception as e:
        logger.error(f"Twitter scrape failed: {e}")
        return []
