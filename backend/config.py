import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Stock video
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY: str = os.getenv("PIXABAY_API_KEY", "")

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
# Google AI Studio TTS (Gemini)
USE_GOOGLE_TTS: bool = os.getenv("USE_GOOGLE_TTS", "False").lower() == "true"
GOOGLE_AI_STUDIO_API_KEY: str = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
GOOGLE_TTS_VOICE: str = os.getenv("GOOGLE_TTS_VOICE", "Aoede")
GOOGLE_TTS_MODEL: str = os.getenv("GOOGLE_TTS_MODEL", "gemini-2.5-flash-preview-tts")

# OpenRouter for script generation and keyword extraction
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

# Groq for fallback
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

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
REQUIRED_KEYS: list[str] = ["GOOGLE_AI_STUDIO_API_KEY", "PEXELS_API_KEY"]


def validate_env() -> list[str]:
    return [k for k in REQUIRED_KEYS if not os.getenv(k)]
