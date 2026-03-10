from pytrends.request import TrendReq
from utils.logger import get_logger

logger = get_logger(__name__)

def get_google_trends(keywords: list[str]) -> list[str]:
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(keywords[:5], timeframe="now 1-d")
        related = pytrends.related_queries()
        trends = []
        for kw in keywords:
            top = related.get(kw, {}).get("top")
            if top is not None:
                trends.extend(top["query"].tolist()[:5])
        return trends
    except Exception as e:
        logger.error(f"Google Trends fetch failed: {e}")
        return []
