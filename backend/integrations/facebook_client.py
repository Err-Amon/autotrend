import requests
from config import FACEBOOK_ACCESS_TOKEN
from utils.logger import get_logger

logger = get_logger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"

def upload_to_facebook(video_path: str, title: str, description: str, page_id: str) -> str | None:
    try:
        url = f"{GRAPH_URL}/{page_id}/videos"
        with open(video_path, "rb") as f:
            res = requests.post(
                url,
                data={"title": title, "description": description, "access_token": FACEBOOK_ACCESS_TOKEN},
                files={"source": f},
                timeout=120,
            )
        res.raise_for_status()
        video_id = res.json().get("id")
        logger.info(f"Facebook upload complete: {video_id}")
        return video_id
    except Exception as e:
        logger.error(f"Facebook upload failed: {e}")
        return None
