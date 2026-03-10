import praw
from config import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT
from utils.logger import get_logger

logger = get_logger(__name__)

def get_reddit_trends(subreddits: list[str], limit: int = 10) -> list[str]:
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        trends = []
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=limit):
                trends.append(post.title)
        return trends
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
        return []
