import os
from utils.logger import get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
CLIENT_SECRETS_FILE = "client_secrets.json"


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning(f"Could not load {TOKEN_FILE}: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"{CLIENT_SECRETS_FILE} not found. "
                    "Download it from Google Cloud Console (OAuth 2.0 Desktop App) "
                    "and place it in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info(f"YouTube credentials saved to {TOKEN_FILE}")

    return creds


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
) -> str | None:
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = _get_credentials()
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        logger.info(f"YouTube upload complete. Video ID: {video_id}")
        return video_id

    except FileNotFoundError as e:
        logger.error(str(e))
        return None
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        return None
