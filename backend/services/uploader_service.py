from integrations.youtube_client import upload_to_youtube
from integrations.facebook_client import upload_to_facebook
from integrations.instagram_client import upload_to_instagram
from integrations.groq_client import groq_chat
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_metadata(script: str, niche: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": (
                f"Given this video script:\n{script[:300]}\n\n"
                f"Generate a JSON object with: title (max 80 chars), description (max 200 chars), "
                f"hashtags (list of 10 strings without #). Niche: {niche}. Return only valid JSON."
            ),
        }
    ]
    response = groq_chat(messages, max_tokens=300)
    try:
        import json
        cleaned = response.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned)
    except Exception:
        return {
            "title": f"Amazing {niche} Facts",
            "description": f"Discover incredible facts about {niche}.",
            "hashtags": [niche.replace(" ", ""), "shorts", "viral"],
        }

def upload_to_platforms(video_path: str, script: str, niche: str, platforms: list[str], config: dict) -> dict:
    metadata = generate_metadata(script, niche)
    title = metadata.get("title", f"{niche} Facts")
    description = metadata.get("description", "")
    tags = metadata.get("hashtags", [])
    results = {}

    if "youtube" in platforms:
        vid_id = upload_to_youtube(video_path, title, description, tags)
        results["youtube"] = vid_id

    if "facebook" in platforms:
        page_id = config.get("facebook_page_id", "")
        vid_id = upload_to_facebook(video_path, title, description, page_id)
        results["facebook"] = vid_id

    if "instagram" in platforms:
        ig_user_id = config.get("instagram_user_id", "")
        video_url = config.get("video_public_url", "")
        caption = f"{title}\n\n{description}\n\n" + " ".join(f"#{t}" for t in tags)
        media_id = upload_to_instagram(video_url, caption, ig_user_id)
        results["instagram"] = media_id

    return results
