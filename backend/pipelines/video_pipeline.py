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

# Pipeline step labels — used for progress callbacks and logging
STEPS = [
    "collecting_trends",
    "filtering_trends",
    "generating_script",
    "generating_voice",
    "fetching_clips",
    "generating_subtitles",
    "assembling_video",
    "uploading",
    "complete",
]


def run_pipeline(
    niche: str,
    platforms: list[str],
    upload_config: dict,
    on_progress: callable = None,
) -> dict:
    job_id = str(uuid.uuid4())[:8]
    result = {
        "job_id": job_id,
        "niche": niche,
        "status": "started",
        "step": "",
        "error": None,
        "video_path": None,
        "uploads": {},
    }

    def progress(step: str, detail: str = ""):
        result["step"] = step
        msg = f"[{job_id}] {step}" + (f": {detail}" if detail else "")
        logger.info(msg)
        if on_progress:
            try:
                on_progress(job_id, step, detail)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    try:
        ensure_storage_dirs()

        progress("collecting_trends", niche)
        trends = collect_trends(niche)
        if not trends:
            raise PipelineError(
                "No trends could be collected. Check API credentials and network."
            )

        progress("filtering_trends", f"{len(trends)} raw trends")
        filtered = filter_trends_for_niche(trends, niche)
        if not filtered:
            raise PipelineError("Trend filtering returned no results.")

        topic = filtered[0]
        logger.info(f"[{job_id}] Selected topic: '{topic}'")

        progress("generating_script", topic)
        script = generate_script(topic, niche, job_id)
        if not script:
            raise PipelineError(f"Script generation failed for topic: '{topic}'")

        progress("generating_voice")
        audio_path = generate_voice(script, job_id)
        if not audio_path:
            raise PipelineError(
                "Voice generation failed. Ensure Piper TTS is installed and the model file exists."
            )

        progress("fetching_clips", topic)
        clips = fetch_clips_for_script(script, job_id)
        if not clips:
            raise PipelineError(
                "No video clips could be fetched. Check PEXELS_API_KEY and PIXABAY_API_KEY."
            )

        progress("generating_subtitles")
        audio_duration = get_audio_duration(audio_path)
        subtitle_path = generate_subtitles(script, audio_duration, job_id)
        if not subtitle_path:
            logger.warning(f"[{job_id}] Subtitles failed — continuing without them")

        progress("assembling_video")
        video_path = assemble_video(clips, audio_path, subtitle_path, job_id)
        if not video_path:
            raise PipelineError("Video assembly failed. Check FFmpeg installation.")

        result["video_path"] = video_path
        result["status"] = "assembled"
        logger.info(f"[{job_id}] Video assembled: {video_path}")

        if platforms:
            progress("uploading", ", ".join(platforms))
            uploads = upload_to_platforms(
                video_path, script, niche, platforms, upload_config
            )
            result["uploads"] = uploads
        else:
            logger.info(f"[{job_id}] No platforms selected, skipping upload")
        result["status"] = "complete"
        progress("complete", video_path)

    except PipelineError as e:
        logger.error(f"[{job_id}] Pipeline error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    except Exception as e:
        logger.error(f"[{job_id}] Unexpected pipeline failure: {e}", exc_info=True)
        result["status"] = "failed"
        result["error"] = f"Unexpected error: {e}"

    finally:
        # Always clean up temp files regardless of outcome
        try:
            clean_job_files(job_id)
        except Exception as e:
            logger.warning(f"[{job_id}] Cleanup failed: {e}")

    return result


def run_queue(
    jobs: list[dict],
    on_progress: callable = None,
    on_job_complete: callable = None,
) -> list[dict]:
    if not jobs:
        logger.warning("Queue received with no jobs")
        return []

    results = []
    total = len(jobs)
    logger.info(f"Queue started: {total} job(s)")

    for index, job in enumerate(jobs):
        niche = job.get("niche", "Technology")
        platforms = job.get("platforms", [])
        upload_config = job.get("upload_config", {})

        logger.info(f"Queue: starting job {index + 1}/{total} — niche={niche}")

        result = run_pipeline(
            niche=niche,
            platforms=platforms,
            upload_config=upload_config,
            on_progress=on_progress,
        )

        results.append(result)

        if on_job_complete:
            try:
                on_job_complete(index, total, result)
            except Exception as e:
                logger.warning(f"on_job_complete callback error: {e}")

        status = result.get("status")
        logger.info(
            f"Queue: job {index + 1}/{total} finished "
            f"(status={status}, job_id={result.get('job_id')})"
        )

    completed = sum(1 for r in results if r["status"] == "complete")
    failed = sum(1 for r in results if r["status"] == "failed")
    logger.info(
        f"Queue complete — {completed} succeeded, {failed} failed out of {total}"
    )

    return results


class PipelineError(Exception):
    pass
