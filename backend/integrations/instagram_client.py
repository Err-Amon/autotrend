import time
import requests
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID
from utils.logger import get_logger

logger = get_logger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"
STATUS_POLL_INTERVAL = 5  # seconds between status checks
STATUS_POLL_MAX = 24  # max polls before giving up (2 minutes total)


def upload_to_instagram(
    video_url: str,
    caption: str,
    ig_user_id: str = "",
) -> str | None:
    if not INSTAGRAM_ACCESS_TOKEN:
        logger.error("INSTAGRAM_ACCESS_TOKEN is not set")
        return None

    target_user_id = ig_user_id or INSTAGRAM_USER_ID
    if not target_user_id:
        logger.error("Instagram user_id is not set")
        return None

    if not video_url.startswith("https://"):
        logger.error(f"Instagram requires a public HTTPS video URL. Got: {video_url}")
        return None

    try:
        # Step 1: Create media container
        logger.info("Instagram: creating media container")
        container_res = requests.post(
            f"{GRAPH_URL}/{target_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption[:2200],
                "share_to_feed": "true",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        container_res.raise_for_status()
        container_id = container_res.json().get("id")

        if not container_id:
            logger.error(
                f"Instagram did not return container id: {container_res.json()}"
            )
            return None

        logger.info(
            f"Instagram: container created ({container_id}), waiting for processing"
        )

        # Step 2: Poll until container is ready
        for poll in range(STATUS_POLL_MAX):
            time.sleep(STATUS_POLL_INTERVAL)
            status_res = requests.get(
                f"{GRAPH_URL}/{container_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": INSTAGRAM_ACCESS_TOKEN,
                },
                timeout=15,
            )
            status_res.raise_for_status()
            status_data = status_res.json()
            status_code = status_data.get("status_code", "")

            logger.info(
                f"Instagram container status: {status_code} (poll {poll + 1}/{STATUS_POLL_MAX})"
            )

            if status_code == "FINISHED":
                break
            if status_code == "ERROR":
                logger.error(f"Instagram media processing failed: {status_data}")
                return None
        else:
            logger.error("Instagram media container did not finish processing in time")
            return None

        # Step 3: Publish
        logger.info("Instagram: publishing Reel")
        publish_res = requests.post(
            f"{GRAPH_URL}/{target_user_id}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        publish_res.raise_for_status()
        media_id = publish_res.json().get("id")

        logger.info(f"Instagram upload complete. Media ID: {media_id}")
        return media_id

    except requests.exceptions.Timeout:
        logger.error("Instagram API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"Instagram HTTP error {e.response.status_code}: {e.response.text}"
        )
        return None
    except Exception as e:
        logger.error(f"Instagram upload failed: {e}")
        return None
