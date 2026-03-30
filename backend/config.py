import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# LLM
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Stock video
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY: str = os.getenv("PIXABAY_API_KEY", "")

# Reddit
REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_SECRET: str = os.getenv("REDDIT_SECRET", "")
REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "AutoTrendBot/1.0")

# YouTube
YOUTUBE_CLIENT_ID: str = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")

# Facebook
FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")

# Instagram
INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID: str = os.getenv("INSTAGRAM_USER_ID", "")

# Piper TTS
PIPER_EXECUTABLE: str = os.getenv("PIPER_EXECUTABLE", "piper")
PIPER_MODEL: str = os.getenv("PIPER_MODEL", "en_US-lessac-medium")
PIPER_MODEL_PATH: str = os.getenv(
    "PIPER_MODEL_PATH",
    str(PROJECT_ROOT / "models" / "en_US-lessac-medium.onnx"),
)

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Storage — absolute paths, safe regardless of working directory
STORAGE_BASE: Path = PROJECT_ROOT / "backend" / "storage"
SCRIPTS_DIR: str = str(STORAGE_BASE / "scripts")
AUDIO_DIR: str = str(STORAGE_BASE / "audio")
CLIPS_DIR: str = str(STORAGE_BASE / "clips")
SUBTITLES_DIR: str = str(STORAGE_BASE / "subtitles")
FINAL_VIDEOS_DIR: str = str(STORAGE_BASE / "final_videos")
LOGS_DIR: str = str(PROJECT_ROOT / "logs")

# Niches
NICHES: list[str] = [
    "Islamic History",
    "Technology",
    "Motivation",
    "Animals",
    "Finance",
    "Space & Science",
]

# Video output
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VIDEO_FPS: int = 30

# Minimum required keys for pipeline to run
REQUIRED_KEYS: list[str] = ["GROQ_API_KEY", "PEXELS_API_KEY"]


def validate_env() -> list[str]:
    return [k for k in REQUIRED_KEYS if not os.getenv(k)]
