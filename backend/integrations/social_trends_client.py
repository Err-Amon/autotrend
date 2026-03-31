import requests
import xml.etree.ElementTree as ET
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {"User-Agent": "AutoTrendBot/1.0"}

# YouTube RSS feeds for trending videos by category
# These are Google's own public RSS endpoints — no API key required
YOUTUBE_CATEGORY_RSS: dict[str, str] = {
    "Technology": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVHFbw7woebKtRljqyntYDQ",
    "Science": "https://www.youtube.com/feeds/videos.xml?channel_id=UCsXVk37bltHxD1rDPwtNM8Q",
    "Finance": "https://www.youtube.com/feeds/videos.xml?channel_id=UCV6KDgJskWaEckne5aPA0aQ",
    "Motivation": "https://www.youtube.com/feeds/videos.xml?channel_id=UCpvg0uZH-oxmCagOGCKHpnQ",
    "Animals": "https://www.youtube.com/feeds/videos.xml?channel_id=UCF9IOB2TExg3QIBupFtBDxg",
}

# YouTube trending RSS by region (global trending, no key needed)
YOUTUBE_TRENDING_RSS = "https://www.youtube.com/feeds/videos.xml?chart=0&gl=US&hl=en"

# HackerNews Algolia API — top stories last 24h, completely free
HN_API_URL = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={limit}"

# Niche mapping to HackerNews query terms
HN_NICHE_QUERIES: dict[str, str] = {
    "Technology": "https://hn.algolia.com/api/v1/search?tags=front_page&query=tech&hitsPerPage=10",
    "Finance": "https://hn.algolia.com/api/v1/search?tags=front_page&query=finance+money&hitsPerPage=10",
    "Space & Science": "https://hn.algolia.com/api/v1/search?tags=front_page&query=science+space&hitsPerPage=10",
    "Motivation": "https://hn.algolia.com/api/v1/search?tags=front_page&query=productivity&hitsPerPage=10",
}


def get_social_trends(niche: str, limit: int = 10) -> list[str]:
    trends: list[str] = []

    trends.extend(_fetch_youtube_trends(niche, limit=limit))
    trends.extend(_fetch_hackernews_trends(niche, limit=limit))

    # Deduplicate
    seen = set()
    unique = []
    for t in trends:
        key = t.lower().strip()
        if key not in seen and len(t.strip()) > 8:
            seen.add(key)
            unique.append(t.strip())

    logger.info(f"Social trends: {len(unique)} items for niche '{niche}'")
    return unique[:limit]


def _fetch_youtube_trends(niche: str, limit: int = 8) -> list[str]:
    titles = []

    # Try niche-specific channel first
    feed_url = YOUTUBE_CATEGORY_RSS.get(niche, YOUTUBE_TRENDING_RSS)

    for url in [feed_url, YOUTUBE_TRENDING_RSS]:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                continue

            root = ET.fromstring(response.content)
            # YouTube RSS uses Atom format
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)

            for entry in entries[:limit]:
                title_el = entry.find("atom:title", ns)
                if title_el is not None and title_el.text:
                    title = title_el.text.strip()
                    if len(title) > 8:
                        titles.append(title)

            if titles:
                logger.info(f"YouTube RSS: {len(titles)} titles for '{niche}'")
                return titles

        except requests.exceptions.Timeout:
            logger.warning(f"YouTube RSS timed out: {url}")
            continue
        except ET.ParseError as e:
            logger.warning(f"YouTube RSS parse error: {e}")
            continue
        except Exception as e:
            logger.warning(f"YouTube RSS failed: {e}")
            continue

    return titles


def _fetch_hackernews_trends(niche: str, limit: int = 8) -> list[str]:
    titles = []

    url = HN_NICHE_QUERIES.get(niche, HN_API_URL.format(limit=limit))

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.warning(f"HackerNews API returned {response.status_code}")
            return []

        data = response.json()
        hits = data.get("hits", [])

        for hit in hits[:limit]:
            title = (hit.get("title") or "").strip()
            if title and len(title) > 8:
                titles.append(title)

        logger.info(f"HackerNews: {len(titles)} stories for '{niche}'")

    except requests.exceptions.Timeout:
        logger.warning("HackerNews API timed out")
    except Exception as e:
        logger.warning(f"HackerNews fetch failed: {e}")

    return titles
