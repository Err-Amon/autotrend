import os
import requests
from config import PEXELS_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
CHUNK_SIZE = 8192


def fetch_pexels_clips(
    query: str,
    clips_dir: str,
    job_id: str,
    count: int = 3,
    file_prefix: str = "pexels",
) -> list[str]:
    if not PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY is not set")
        return []

    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": count * 2,  # Fetch more to filter for best matches
        "orientation": "portrait",
        "size": "medium",
        "locale": "en-US",
    }

    paths = []

    try:
        res = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        videos = res.json().get("videos", [])

        if not videos:
            logger.warning(f"Pexels: no videos found for query '{query}'")
            return []

        for i, video in enumerate(videos[:count]):
            files = video.get("video_files", [])
            if not files:
                continue

            # Prefer SD portrait — smallest usable size for 8GB RAM machines
            target = next(
                (
                    f
                    for f in files
                    if f.get("quality") == "sd" and f.get("width", 9999) <= 720
                ),
                next((f for f in files if f.get("quality") == "sd"), files[0]),
            )

            url = target.get("link")
            if not url:
                continue

            path = os.path.join(clips_dir, f"{file_prefix}_{i}.mp4")
            if _stream_download(url, path):
                paths.append(path)

    except requests.exceptions.Timeout:
        logger.error("Pexels API request timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Pexels HTTP error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"Pexels fetch failed: {e}")

    logger.info(f"Pexels: downloaded {len(paths)} clips for '{query}'")
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
