import praw
from config import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT
from utils.logger import get_logger

logger = get_logger(__name__)


def get_reddit_trends(subreddits: list[str], limit: int = 10) -> list[str]:
    if not REDDIT_CLIENT_ID or not REDDIT_SECRET:
        logger.warning("Reddit credentials not set, skipping Reddit trends")
        return []

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        trends = []
        for sub in subreddits:
            try:
                for post in reddit.subreddit(sub).hot(limit=limit):
                    if not post.stickied and len(post.title) > 10:
                        trends.append(post.title)
            except Exception as e:
                logger.warning(f"Failed to fetch subreddit r/{sub}: {e}")
                continue

        unique = list(dict.fromkeys(trends))
        logger.info(f"Reddit: collected {len(unique)} trends from {subreddits}")
        return unique

    except praw.exceptions.PRAWException as e:
        logger.error(f"Reddit PRAW error: {e}")
        return []
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
        return []
