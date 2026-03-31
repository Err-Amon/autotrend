import os
import shutil
from config import SCRIPTS_DIR, AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, FINAL_VIDEOS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIRS = [SCRIPTS_DIR, AUDIO_DIR, CLIPS_DIR, SUBTITLES_DIR, FINAL_VIDEOS_DIR]


def ensure_storage_dirs():
    for d in BASE_DIRS:
        os.makedirs(d, exist_ok=True)
    logger.info("Storage directories verified")


def get_job_dirs(job_id: str) -> dict[str, str]:
    return {
        "audio": os.path.join(AUDIO_DIR, job_id),
        "clips": os.path.join(CLIPS_DIR, job_id),
        "subtitles": os.path.join(SUBTITLES_DIR, job_id),
        "scripts": os.path.join(SCRIPTS_DIR, job_id),
        "final": os.path.join(FINAL_VIDEOS_DIR, job_id),
    }


def create_job_dirs(job_id: str) -> dict[str, str]:
    dirs = get_job_dirs(job_id)
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
    logger.info(f"[{job_id}] Job directories created")
    return dirs


def clean_job_workspace(job_id: str):
    dirs = get_job_dirs(job_id)
    to_clean = ["audio", "clips", "subtitles", "scripts"]

    for key in to_clean:
        path = dirs[key]
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logger.info(f"[{job_id}] Cleaned workspace: {path}")
            except Exception as e:
                logger.warning(f"[{job_id}] Could not clean {path}: {e}")


def clean_job_final(job_id: str):
    final_dir = get_job_dirs(job_id)["final"]
    if os.path.exists(final_dir):
        try:
            shutil.rmtree(final_dir)
            logger.info(f"[{job_id}] Cleaned failed job final dir: {final_dir}")
        except Exception as e:
            logger.warning(f"[{job_id}] Could not clean final dir: {e}")


def get_path(directory: str, filename: str) -> str:
    return os.path.join(directory, filename)
