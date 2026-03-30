import os
import requests
from config import PEXELS_API_KEY, CLIPS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
CHUNK_SIZE = 8192


def fetch_pexels_clips(query: str, job_id: str, count: int = 3) -> list[str]:
    if not PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY is not set")
        return []

    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": count,
        "orientation": "portrait",
        "size": "medium",
    }

    paths = []

    try:
        res = requests.get(
            PEXELS_VIDEO_URL,
            headers=headers,
            params=params,
            timeout=15,
        )
        res.raise_for_status()
        videos = res.json().get("videos", [])

        if not videos:
            logger.warning(f"Pexels: no videos found for query '{query}'")
            return []

        for i, video in enumerate(videos[:count]):
            files = video.get("video_files", [])
            if not files:
                continue

            # Prefer SD quality to keep file sizes small on 8GB RAM machines
            target = next(
                (
                    f
                    for f in files
                    if f.get("quality") == "sd" and f.get("width", 0) <= 1080
                ),
                files[0],
            )

            url = target.get("link")
            if not url:
                continue

            path = os.path.join(CLIPS_DIR, f"{job_id}_pexels_{i}.mp4")
            success = _stream_download(url, path)
            if success:
                paths.append(path)

    except requests.exceptions.Timeout:
        logger.error("Pexels API request timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"Pexels API HTTP error {e.response.status_code}: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Pexels fetch failed: {e}")

    logger.info(f"Pexels: downloaded {len(paths)} clips for query '{query}'")
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
        logger.error(f"Failed to download clip from {url}: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False
