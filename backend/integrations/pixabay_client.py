import requests
import os
from config import PIXABAY_API_KEY, CLIPS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

PIXABAY_URL = "https://pixabay.com/api/videos/"

def fetch_pixabay_clips(query: str, job_id: str, count: int = 3) -> list[str]:
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": count,
        "video_type": "film",
    }
    paths = []
    try:
        res = requests.get(PIXABAY_URL, params=params, timeout=15)
        res.raise_for_status()
        hits = res.json().get("hits", [])
        for i, hit in enumerate(hits[:count]):
            url = hit.get("videos", {}).get("medium", {}).get("url")
            if not url:
                continue
            path = os.path.join(CLIPS_DIR, f"{job_id}_pixabay_{i}.mp4")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            paths.append(path)
    except Exception as e:
        logger.error(f"Pixabay fetch failed: {e}")
    return paths
