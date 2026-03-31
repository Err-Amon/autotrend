import requests
import xml.etree.ElementTree as ET
from utils.logger import get_logger

logger = get_logger(__name__)

GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)

NICHE_RSS_FEEDS: dict[str, list[str]] = {
    "Islamic History": [
        "https://news.google.com/rss/search?q=islamic+history+muslim&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=ottoman+empire+muslim+civilization&hl=en-US&gl=US&ceid=US:en",
    ],
    "Technology": [
        "https://news.google.com/rss/search?q=technology+AI+innovation&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.feedburner.com/TechCrunch",
    ],
    "Motivation": [
        "https://news.google.com/rss/search?q=motivation+success+self+improvement&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=productivity+mindset+growth&hl=en-US&gl=US&ceid=US:en",
    ],
    "Animals": [
        "https://news.google.com/rss/search?q=wildlife+animals+nature&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=endangered+species+animal+discovery&hl=en-US&gl=US&ceid=US:en",
    ],
    "Finance": [
        "https://news.google.com/rss/search?q=personal+finance+investing+money&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=stock+market+financial+tips&hl=en-US&gl=US&ceid=US:en",
    ],
    "Space & Science": [
        "https://news.google.com/rss/search?q=space+exploration+NASA+discovery&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=science+breakthrough+research&hl=en-US&gl=US&ceid=US:en",
    ],
}

HEADERS = {"User-Agent": "AutoTrendBot/1.0 (RSS Reader)"}

# Keywords that indicate promotional, sponsored, or ad content — these are
# NOT genuine news/events and should be excluded from the topic pool.
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
    """Return True if the headline looks like an ad or promotional content."""
    lower = text.lower()
    return any(kw in lower for kw in _AD_BLOCKLIST)


def get_news_trends(niche: str, limit: int = 15) -> list[str]:
    feeds = NICHE_RSS_FEEDS.get(
        niche, [GOOGLE_NEWS_RSS.format(query=requests.utils.quote(niche))]
    )

    headlines = []

    for feed_url in feeds:
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"RSS feed returned {response.status_code}: {feed_url}")
                continue

            root = ET.fromstring(response.content)
            items = root.findall(".//item/title")

            for item in items:
                text = (item.text or "").strip()
                # Strip source attribution appended by Google News e.g. " - BBC News"
                if " - " in text:
                    text = text.rsplit(" - ", 1)[0].strip()
                if text and len(text) > 10 and not _is_promotional(text):
                    headlines.append(text)
                elif text and _is_promotional(text):
                    logger.debug(f"RSS: skipped promotional headline: {text!r}")

            if headlines:
                logger.info(f"RSS: fetched {len(headlines)} headlines from {feed_url}")

        except requests.exceptions.Timeout:
            logger.warning(f"RSS feed timed out: {feed_url}")
            continue
        except ET.ParseError as e:
            logger.warning(f"RSS feed parse error ({feed_url}): {e}")
            continue
        except Exception as e:
            logger.warning(f"RSS feed failed ({feed_url}): {e}")
            continue

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for h in headlines:
        key = h.lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)

    result = unique[:limit]
    logger.info(f"News RSS: {len(result)} unique headlines for niche '{niche}'")
    return result
