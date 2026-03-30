import requests
from utils.logger import get_logger

logger = get_logger(__name__)

# snscrape is no longer reliable due to Twitter/X API restrictions.
# This module uses the free Nitter RSS fallback instead.
# Nitter instances are public mirrors of Twitter content.

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]


def get_twitter_trends(query: str, limit: int = 10) -> list[str]:
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/search/rss?q={requests.utils.quote(query)}&f=tweets"
            response = requests.get(
                url, timeout=10, headers={"User-Agent": "AutoTrendBot/1.0"}
            )

            if response.status_code != 200:
                continue

            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
            items = root.findall(".//item/title")

            trends = []
            for item in items[:limit]:
                text = item.text or ""
                text = text.strip()
                if text and len(text) > 10:
                    trends.append(text)

            if trends:
                logger.info(
                    f"Twitter/Nitter: collected {len(trends)} trends via {instance}"
                )
                return trends

        except requests.exceptions.Timeout:
            logger.warning(f"Nitter instance timed out: {instance}")
            continue
        except Exception as e:
            logger.warning(f"Nitter instance failed ({instance}): {e}")
            continue

    logger.warning("All Nitter instances failed, returning empty Twitter trends")
    return []
