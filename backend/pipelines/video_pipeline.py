import uuid
from services.trend_service import collect_trends
from services.niche_filter_service import filter_trends_for_niche
from services.script_service import generate_script
from services.voice_service import generate_voice
from services.video_fetcher import fetch_clips_for_script
from services.video_editor import assemble_video, get_audio_duration
from services.subtitle_service import generate_subtitles
from services.uploader_service import upload_to_platforms
from utils.file_manager import ensure_storage_dirs, clean_job_files
from utils.logger import get_logger

logger = get_logger(__name__)

def run_pipeline(niche: str, platforms: list[str], upload_config: dict, on_progress=None) -> dict:
    job_id = str(uuid.uuid4())[:8]
    result = {"job_id": job_id, "status": "started", "error": None, "video_path": None, "uploads": {}}

    def progress(step: str):
        logger.info(f"[{job_id}] {step}")
        if on_progress:
            on_progress(job_id, step)

    try:
        ensure_storage_dirs()

        progress("Collecting trends")
        trends = collect_trends(niche)
        if not trends:
            raise ValueError("No trends collected")

        progress("Filtering trends for niche")
        filtered = filter_trends_for_niche(trends, niche)
        topic = filtered[0] if filtered else trends[0]

        progress(f"Generating script for: {topic}")
        script = generate_script(topic, niche, job_id)
        if not script:
            raise ValueError("Script generation failed")

        progress("Generating voice narration")
        audio_path = generate_voice(script, job_id)
        if not audio_path:
            raise ValueError("Voice generation failed")

        progress("Fetching stock video clips")
        clips = fetch_clips_for_script(script, job_id)
        if not clips:
            raise ValueError("No video clips fetched")

        progress("Generating subtitles")
        duration = get_audio_duration(audio_path)
        subtitle_path = generate_subtitles(script, duration, job_id)

        progress("Assembling final video")
        video_path = assemble_video(clips, audio_path, subtitle_path, job_id)
        if not video_path:
            raise ValueError("Video assembly failed")

        result["video_path"] = video_path
        result["status"] = "assembled"

        if platforms:
            progress("Uploading to platforms")
            uploads = upload_to_platforms(video_path, script, niche, platforms, upload_config)
            result["uploads"] = uploads

        result["status"] = "complete"
        progress("Pipeline complete")

    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
    finally:
        clean_job_files(job_id)

    return result


def run_queue(jobs: list[dict], on_progress=None) -> list[dict]:
    results = []
    for job in jobs:
        logger.info(f"Starting job: {job}")
        result = run_pipeline(
            niche=job.get("niche", "Technology"),
            platforms=job.get("platforms", []),
            upload_config=job.get("upload_config", {}),
            on_progress=on_progress,
        )
        results.append(result)
    return results
