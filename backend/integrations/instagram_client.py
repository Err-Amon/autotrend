import requests
from config import INSTAGRAM_ACCESS_TOKEN
from utils.logger import get_logger

logger = get_logger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"

def upload_to_instagram(video_url: str, caption: str, ig_user_id: str) -> str | None:
    try:
        container_res = requests.post(
            f"{GRAPH_URL}/{ig_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        container_res.raise_for_status()
        container_id = container_res.json().get("id")

        publish_res = requests.post(
            f"{GRAPH_URL}/{ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=30,
        )
        publish_res.raise_for_status()
        media_id = publish_res.json().get("id")
        logger.info(f"Instagram upload complete: {media_id}")
        return media_id
    except Exception as e:
        logger.error(f"Instagram upload failed: {e}")
        return None
