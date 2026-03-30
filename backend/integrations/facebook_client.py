import os
import requests
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID
from utils.logger import get_logger

logger = get_logger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"
CHUNK_SIZE = 1024 * 1024  # 1MB


def upload_to_facebook(
    video_path: str,
    title: str,
    description: str,
    page_id: str = "",
) -> str | None:
    if not FACEBOOK_ACCESS_TOKEN:
        logger.error("FACEBOOK_ACCESS_TOKEN is not set")
        return None

    target_page_id = page_id or FACEBOOK_PAGE_ID
    if not target_page_id:
        logger.error("Facebook page_id is not set")
        return None

    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    file_size = os.path.getsize(video_path)
    logger.info(f"Uploading to Facebook ({file_size / 1024 / 1024:.1f}MB)")

    try:
        # Step 1: Initialize resumable upload session
        init_res = requests.post(
            f"{GRAPH_URL}/{target_page_id}/videos",
            data={
                "upload_phase": "start",
                "file_size": file_size,
                "access_token": FACEBOOK_ACCESS_TOKEN,
            },
            timeout=30,
        )
        init_res.raise_for_status()
        init_data = init_res.json()
        upload_session_id = init_data.get("upload_session_id")
        video_id = init_data.get("video_id")

        if not upload_session_id:
            logger.error(f"Facebook did not return upload_session_id: {init_data}")
            return None

        # Step 2: Upload file in chunks
        offset = 0
        with open(video_path, "rb") as f:
            while offset < file_size:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                transfer_res = requests.post(
                    f"{GRAPH_URL}/{target_page_id}/videos",
                    data={
                        "upload_phase": "transfer",
                        "upload_session_id": upload_session_id,
                        "start_offset": offset,
                        "access_token": FACEBOOK_ACCESS_TOKEN,
                    },
                    files={"video_file_chunk": chunk},
                    timeout=60,
                )
                transfer_res.raise_for_status()
                transfer_data = transfer_res.json()
                offset = int(transfer_data.get("start_offset", offset + len(chunk)))

        # Step 3: Finish upload
        finish_res = requests.post(
            f"{GRAPH_URL}/{target_page_id}/videos",
            data={
                "upload_phase": "finish",
                "upload_session_id": upload_session_id,
                "title": title[:255],
                "description": description[:2048],
                "access_token": FACEBOOK_ACCESS_TOKEN,
            },
            timeout=30,
        )
        finish_res.raise_for_status()

        logger.info(f"Facebook upload complete. Video ID: {video_id}")
        return video_id

    except requests.exceptions.Timeout:
        logger.error("Facebook upload request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Facebook HTTP error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Facebook upload failed: {e}")
        return None
