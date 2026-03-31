import requests
import xml.etree.ElementTree as ET
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {"User-Agent": "AutoTrendBot/1.0"}

# Shared promotional-content blocklist (same logic as news_rss_client)
_AD_BLOCKLIST = {
    "sponsored",
    "advertisement",
    "advertorial",
    "promoted",
    "promotion",
    "buy now",
    "shop now",
    "sale",
    "discount",
    "coupon",
    "promo code",
    "free trial",
    "sign up",
    "subscribe now",
    "limited offer",
    "limited time",
    "best deal",
    "best price",
    "cheap",
    "affordable",
    "get started",
    "enroll now",
    "enroll today",
    "register now",
    "join now",
    "course",
    "bootcamp",
    "masterclass",
    "webinar",
    "workshop",
    "learn how to",
    "how to make money",
    "earn money",
    "passive income",
    "make $",
    "earn $",
    "get paid",
    "work from home",
    "affiliate",
    "referral",
    "partner",
    "sponsored by",
    "ad:",
    "[ad]",
    "[sponsored]",
    "[promo]",
}


def _is_promotional(text: str) -> bool:
    """Return True if the title looks like an ad or promotional content."""
    lower = text.lower()
    return any(kw in lower for kw in _AD_BLOCKLIST)


# YouTube channel RSS feeds per niche — Google's own public endpoints, no key needed
YOUTUBE_CATEGORY_RSS: dict[str, str] = {
    "Technology": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVHFbw7woebKtRljqyntYDQ",
    "Space & Science": "https://www.youtube.com/feeds/videos.xml?channel_id=UCsXVk37bltHxD1rDPwtNM8Q",
    "Finance": "https://www.youtube.com/feeds/videos.xml?channel_id=UCV6KDgJskWaEckne5aPA0aQ",
    "Motivation": "https://www.youtube.com/feeds/videos.xml?channel_id=UCpvg0uZH-oxmCagOGCKHpnQ",
    "Animals": "https://www.youtube.com/feeds/videos.xml?channel_id=UCF9IOB2TExg3QIBupFtBDxg",
}

# General YouTube trending fallback (no key needed)
YOUTUBE_TRENDING_RSS = "https://www.youtube.com/feeds/videos.xml?chart=0&gl=US&hl=en"

# HackerNews Algolia API — completely free, no key, no rate limit for normal usage
HN_NICHE_QUERIES: dict[str, str] = {
    "Technology": "https://hn.algolia.com/api/v1/search?tags=front_page&query=tech&hitsPerPage=10",
    "Finance": "https://hn.algolia.com/api/v1/search?tags=front_page&query=finance+money&hitsPerPage=10",
    "Space & Science": "https://hn.algolia.com/api/v1/search?tags=front_page&query=science+space&hitsPerPage=10",
    "Motivation": "https://hn.algolia.com/api/v1/search?tags=front_page&query=productivity&hitsPerPage=10",
}
HN_DEFAULT_URL = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10"


def get_social_trends(niche: str, limit: int = 10) -> list[str]:
    trends: list[str] = []
    trends.extend(_fetch_youtube_trends(niche, limit=limit))
    trends.extend(_fetch_hackernews_trends(niche, limit=limit))

    seen: set[str] = set()
    unique: list[str] = []
    for t in trends:
        key = t.lower().strip()
        if key not in seen and len(t.strip()) > 8:
            seen.add(key)
            unique.append(t.strip())

    logger.info(f"Social trends: {len(unique)} items for niche '{niche}'")
    return unique[:limit]


def _fetch_youtube_trends(niche: str, limit: int = 8) -> list[str]:
    niche_url = YOUTUBE_CATEGORY_RSS.get(niche)

    if niche_url and niche_url != YOUTUBE_TRENDING_RSS:
        urls = [niche_url, YOUTUBE_TRENDING_RSS]
    else:
        urls = [YOUTUBE_TRENDING_RSS]

    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"YouTube RSS {url} returned {response.status_code}")
                continue

            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)

            titles = []
            for entry in entries[:limit]:
                title_el = entry.find("atom:title", ns)
                if title_el is not None and title_el.text:
                    title = title_el.text.strip()
                    if len(title) > 8 and not _is_promotional(title):
                        titles.append(title)
                    elif title and _is_promotional(title):
                        logger.debug(f"YouTube: skipped promotional title: {title!r}")

            if titles:
                logger.info(
                    f"YouTube RSS: {len(titles)} titles for '{niche}' via {url}"
                )
                return titles

        except requests.exceptions.Timeout:
            logger.warning(f"YouTube RSS timed out: {url}")
        except ET.ParseError as e:
            logger.warning(f"YouTube RSS parse error ({url}): {e}")
        except Exception as e:
            logger.warning(f"YouTube RSS failed ({url}): {e}")

    return []


def _fetch_hackernews_trends(niche: str, limit: int = 8) -> list[str]:
    url = HN_NICHE_QUERIES.get(niche, HN_DEFAULT_URL)
    titles: list[str] = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.warning(f"HackerNews API returned {response.status_code}")
            return []

        hits = response.json().get("hits", [])
        for hit in hits[:limit]:
            title = (hit.get("title") or "").strip()
            if title and len(title) > 8 and not _is_promotional(title):
                titles.append(title)
            elif title and _is_promotional(title):
                logger.debug(f"HackerNews: skipped promotional story: {title!r}")

        logger.info(f"HackerNews: {len(titles)} stories for '{niche}'")

    except requests.exceptions.Timeout:
        logger.warning("HackerNews API timed out")
    except Exception as e:
        logger.warning(f"HackerNews fetch failed: {e}")

    return titles
