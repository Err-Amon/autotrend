import requests
import os
from config import PEXELS_API_KEY, CLIPS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"

def fetch_pexels_clips(query: str, job_id: str, count: int = 3) -> list[str]:
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": count, "orientation": "portrait"}
    paths = []
    try:
        res = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        videos = res.json().get("videos", [])
        for i, video in enumerate(videos[:count]):
            files = video.get("video_files", [])
            hd = next((f for f in files if f.get("quality") == "sd"), files[0] if files else None)
            if not hd:
                continue
            url = hd["link"]
            path = os.path.join(CLIPS_DIR, f"{job_id}_pexels_{i}.mp4")
            _download_file(url, path)
            paths.append(path)
    except Exception as e:
        logger.error(f"Pexels fetch failed: {e}")
    return paths

def _download_file(url: str, path: str):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
