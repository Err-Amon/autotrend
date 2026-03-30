from pytrends.request import TrendReq
from utils.logger import get_logger

logger = get_logger(__name__)


def get_google_trends(keywords: list[str]) -> list[str]:
    if not keywords:
        return []

    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        # pytrends accepts max 5 keywords per payload
        pytrends.build_payload(keywords[:5], timeframe="now 1-d", geo="")

        related = pytrends.related_queries()
        trends = []

        for kw in keywords[:5]:
            data = related.get(kw, {})
            top = data.get("top")
            rising = data.get("rising")

            if top is not None and not top.empty:
                trends.extend(top["query"].tolist()[:5])
            if rising is not None and not rising.empty:
                trends.extend(rising["query"].tolist()[:3])

        unique = list(dict.fromkeys(trends))
        logger.info(
            f"Google Trends: collected {len(unique)} trends for keywords: {keywords}"
        )
        return unique

    except Exception as e:
        logger.error(f"Google Trends fetch failed: {e}")
        return []
