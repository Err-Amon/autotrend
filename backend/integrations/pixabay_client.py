import os
import requests
from config import PIXABAY_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

PIXABAY_URL = "https://pixabay.com/api/videos/"
CHUNK_SIZE = 8192


def fetch_pixabay_clips(
    query: str,
    clips_dir: str,
    job_id: str,
    count: int = 3,
    file_prefix: str = "pixabay",
) -> list[str]:

    if not PIXABAY_API_KEY:
        logger.error("PIXABAY_API_KEY is not set")
        return []

    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": min(count, 20),
        "video_type": "film",
        "safesearch": "true",
    }

    paths = []

    try:
        res = requests.get(PIXABAY_URL, params=params, timeout=15)
        res.raise_for_status()
        hits = res.json().get("hits", [])

        if not hits:
            logger.warning(f"Pixabay: no videos found for query '{query}'")
            return []

        for i, hit in enumerate(hits[:count]):
            videos = hit.get("videos", {})
            # Prefer small over medium to reduce memory pressure
            clip = videos.get("small") or videos.get("medium") or videos.get("large")
            if not clip:
                continue

            url = clip.get("url")
            if not url:
                continue

            path = os.path.join(clips_dir, f"{file_prefix}_{i}.mp4")
            if _stream_download(url, path):
                paths.append(path)

    except requests.exceptions.Timeout:
        logger.error("Pixabay API request timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Pixabay HTTP error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"Pixabay fetch failed: {e}")

    logger.info(f"Pixabay: downloaded {len(paths)} clips for '{query}'")
    return paths


def _stream_download(url: str, path: str) -> bool:
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download clip: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False
