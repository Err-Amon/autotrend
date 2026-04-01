import json
from integrations.gemini_client import gemini_chat
from integrations.youtube_client import upload_to_youtube
from integrations.facebook_client import upload_to_facebook
from integrations.instagram_client import upload_to_instagram
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_metadata(script: str, niche: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": (
                f"You are a social media manager. Based on this video script:\n\n"
                f"{script[:400]}\n\n"
                f"Generate metadata for a {niche} short-form video.\n"
                f"Return ONLY a valid JSON object with these exact keys:\n"
                f"- title: string, max 80 characters, no emojis\n"
                f"- description: string, max 200 characters\n"
                f"- hashtags: array of exactly 10 strings, no # symbol\n\n"
                f"No explanation. No markdown. Valid JSON only."
            ),
        }
    ]

    response = gemini_chat(messages, max_tokens=300)

    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```")
                # parts[1] is the content between first pair of fences
                cleaned = parts[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            metadata = json.loads(cleaned)

            title = str(metadata.get("title", "")).strip()[:100]
            description = str(metadata.get("description", "")).strip()[:2000]
            hashtags = metadata.get("hashtags", [])
            if not isinstance(hashtags, list):
                hashtags = []
            hashtags = [str(h).replace("#", "").strip() for h in hashtags[:20] if h]

            if title and description:
                logger.info(f"Metadata generated: '{title}'")
                return {
                    "title": title,
                    "description": description,
                    "hashtags": hashtags,
                }
            else:
                logger.warning("Metadata missing title or description, using fallback")

        except json.JSONDecodeError as e:
            logger.warning(f"Metadata JSON parse failed: {e}")
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Metadata structure invalid: {e}")

    logger.warning("Using fallback metadata")
    return {
        "title": f"Amazing {niche} Facts You Never Knew",
        "description": f"Discover incredible facts about {niche}. Follow for more!",
        "hashtags": [
            niche.replace(" ", "").lower(),
            "shorts",
            "viral",
            "facts",
            "didyouknow",
            "trending",
            "reels",
            "foryou",
            "fyp",
            "explore",
        ],
    }


def upload_to_platforms(
    video_path: str,
    script: str,
    niche: str,
    platforms: list[str],
    upload_config: dict,
) -> dict:
    if not platforms:
        logger.info("No platforms selected, skipping upload")
        return {}

    metadata = generate_metadata(script, niche)
    title = metadata["title"]
    description = metadata["description"]
    hashtags = metadata["hashtags"]
    caption = f"{title}\n\n{description}\n\n" + " ".join(f"#{h}" for h in hashtags)

    results: dict[str, str | None] = {}

    if "youtube" in platforms:
        logger.info("Uploading to YouTube")
        results["youtube"] = upload_to_youtube(video_path, title, description, hashtags)

    if "facebook" in platforms:
        logger.info("Uploading to Facebook")
        page_id = upload_config.get("facebook_page_id", "")
        results["facebook"] = upload_to_facebook(
            video_path, title, description, page_id
        )

    if "instagram" in platforms:
        logger.info("Uploading to Instagram")
        ig_user_id = upload_config.get("instagram_user_id", "")
        video_url = upload_config.get("video_public_url", "")
        if not video_url:
            logger.warning(
                "Instagram upload skipped: 'video_public_url' not in upload_config. "
                "Instagram requires the video to be hosted at a public HTTPS URL."
            )
            results["instagram"] = None
        else:
            results["instagram"] = upload_to_instagram(video_url, caption, ig_user_id)

    logger.info(f"Upload results: {results}")
    return results
