import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "AutoTrendBot/1.0")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

STORAGE_BASE = "backend/storage"
SCRIPTS_DIR = f"{STORAGE_BASE}/scripts"
AUDIO_DIR = f"{STORAGE_BASE}/audio"
CLIPS_DIR = f"{STORAGE_BASE}/clips"
SUBTITLES_DIR = f"{STORAGE_BASE}/subtitles"
FINAL_VIDEOS_DIR = f"{STORAGE_BASE}/final_videos"

NICHES = [
    "Islamic History",
    "Technology",
    "Motivation",
    "Animals",
    "Finance",
    "Space & Science",
]

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
