import os
from config import SCRIPTS_DIR, AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, FINAL_VIDEOS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DIRS = [SCRIPTS_DIR, AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, FINAL_VIDEOS_DIR]


def ensure_storage_dirs():
    for d in DIRS:
        os.makedirs(d, exist_ok=True)
    logger.info("Storage directories verified")


def clean_job_files(job_id: str):
    for d in [AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR]:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.startswith(job_id):
                path = os.path.join(d, f)
                try:
                    os.remove(path)
                    logger.info(f"Cleaned: {path}")
                except Exception as e:
                    logger.warning(f"Could not delete {path}: {e}")


def get_path(directory: str, filename: str) -> str:
    return os.path.join(directory, filename)
