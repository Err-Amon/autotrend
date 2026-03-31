import uuid
from collections.abc import Callable
from services.trend_service import collect_trends
from services.niche_filter_service import filter_trends_for_niche
from services.script_service import generate_script
from services.voice_service import generate_voice
from services.video_fetcher import fetch_clips_for_script
from services.video_editor import assemble_video, get_audio_duration
from services.subtitle_service import generate_subtitles
from services.uploader_service import upload_to_platforms
from utils.file_manager import create_job_dirs, clean_job_workspace, clean_job_final
from utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline(
    niche: str,
    platforms: list[str],
    upload_config: dict,
    on_progress: Callable | None = None,
) -> dict:
    job_id = str(uuid.uuid4())[:8]
    result: dict = {
        "job_id": job_id,
        "niche": niche,
        "status": "started",
        "step": "",
        "detail": "",
        "error": None,
        "video_path": None,
        "uploads": {},
    }

    job_dirs: dict | None = None

    def progress(step: str, detail: str = ""):
        result["step"] = step
        result["detail"] = detail
        msg = f"[{job_id}] {step}" + (f": {detail}" if detail else "")
        logger.info(msg)
        if on_progress:
            try:
                on_progress(job_id, step, detail)
            except Exception as cb_err:
                logger.warning(f"Progress callback error: {cb_err}")

    try:
        job_dirs = create_job_dirs(job_id)

        # Step 1: Collect trends
        progress("collecting_trends", niche)
        trends = collect_trends(niche)
        if not trends:
            raise PipelineError(
                "No trends collected. Check your network connection. "
                "Google News RSS, YouTube RSS, and HackerNews should all work without credentials."
            )

        # Step 2: Filter trends for niche
        progress("filtering_trends", f"{len(trends)} raw trends")
        filtered = filter_trends_for_niche(trends, niche)
        if not filtered:
            raise PipelineError("Trend filtering returned no results.")

        topic = filtered[0]
        logger.info(f"[{job_id}] Selected topic: '{topic}'")

        # Step 3: Generate script
        progress("generating_script", topic)
        script = generate_script(topic, niche, job_id, scripts_dir=job_dirs["scripts"])
        if not script:
            raise PipelineError(f"Script generation failed for topic: '{topic}'")

        # Step 4: Generate voice narration
        progress("generating_voice")
        audio_path = generate_voice(script, job_id, audio_dir=job_dirs["audio"])
        if not audio_path:
            raise PipelineError(
                "Voice generation failed. "
                "Ensure Piper TTS is installed and PIPER_MODEL_PATH points to the .onnx file."
            )

        # Step 5: Fetch stock video clips
        progress("fetching_clips", topic)
        clips = fetch_clips_for_script(script, job_dirs["clips"], job_id)
        if not clips:
            raise PipelineError(
                "No video clips fetched. Check PEXELS_API_KEY and PIXABAY_API_KEY in .env."
            )

        # Step 6: Generate subtitles
        progress("generating_subtitles")
        audio_duration = get_audio_duration(audio_path)
        subtitle_path = generate_subtitles(
            script,
            audio_duration,
            job_id,
            subtitles_dir=job_dirs["subtitles"],
        )
        if not subtitle_path:
            logger.warning(f"[{job_id}] Subtitles failed — continuing without them")

        # Step 7: Assemble final video
        progress("assembling_video")
        video_path = assemble_video(
            clips,
            audio_path,
            subtitle_path,
            job_id,
            output_dir=job_dirs["final"],
        )
        if not video_path:
            raise PipelineError(
                "Video assembly failed. Verify FFmpeg is installed: run 'ffmpeg -version' in terminal."
            )

        result["video_path"] = video_path
        result["status"] = "assembled"
        clean_job_workspace(job_id)

        # Step 8: Upload to platforms
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
        if job_dirs:
            clean_job_workspace(job_id)
            clean_job_final(job_id)

    except Exception as e:
        logger.error(f"[{job_id}] Unexpected failure: {e}", exc_info=True)
        result["status"] = "failed"
        result["error"] = f"Unexpected error: {e}"
        if job_dirs:
            clean_job_workspace(job_id)
            clean_job_final(job_id)

    return result


def run_queue(
    jobs: list[dict],
    on_progress: Callable | None = None,
    on_job_complete: Callable | None = None,
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

        logger.info(
            f"Queue: job {index + 1}/{total} done "
            f"(status={result.get('status')}, id={result.get('job_id')})"
        )

    completed = sum(1 for r in results if r["status"] == "complete")
    failed = sum(1 for r in results if r["status"] == "failed")
    logger.info(f"Queue done — {completed} succeeded, {failed} failed out of {total}")
    return results


class PipelineError(Exception):
    pass
