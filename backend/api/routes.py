import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, field_validator
from pipelines.video_pipeline import run_pipeline, run_queue
from config import NICHES
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

_jobs: dict[str, dict] = {}


class JobRequest(BaseModel):
    niche: str
    platforms: list[str] = []
    upload_config: dict = {}

    @field_validator("niche")
    @classmethod
    def niche_must_be_valid(cls, v: str) -> str:
        if v not in NICHES:
            raise ValueError(f"Invalid niche '{v}'. Must be one of: {NICHES}")
        return v

    @field_validator("platforms")
    @classmethod
    def platforms_must_be_valid(cls, v: list[str]) -> list[str]:
        allowed = {"youtube", "instagram", "facebook"}
        invalid = [p for p in v if p not in allowed]
        if invalid:
            raise ValueError(
                f"Invalid platforms: {invalid}. Allowed: {sorted(allowed)}"
            )
        return v


class QueueRequest(BaseModel):
    jobs: list[JobRequest]

    @field_validator("jobs")
    @classmethod
    def jobs_must_not_be_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Queue must contain at least one job")
        if len(v) > 20:
            raise ValueError("Queue cannot exceed 20 jobs at a time")
        return v


def _progress_callback(job_id: str, step: str, detail: str = ""):
    if job_id in _jobs:
        _jobs[job_id]["step"] = step
        _jobs[job_id]["detail"] = detail


def _run_single_job(
    tracking_id: str,
    niche: str,
    platforms: list[str],
    upload_config: dict,
):

    _jobs[tracking_id]["status"] = "running"

    result = run_pipeline(
        niche=niche,
        platforms=platforms,
        upload_config=upload_config,
        on_progress=lambda jid, step, detail: _progress_callback(
            tracking_id, step, detail
        ),
    )

    result["tracking_id"] = tracking_id
    _jobs[tracking_id] = result


def _run_queue_jobs(jobs: list[JobRequest], tracking_ids: list[str]):
    """
    Runs queued jobs sequentially. Each job's result is stored under
    its pre-assigned tracking_id so the caller can poll by those IDs.
    """
    for i, job in enumerate(jobs):
        tracking_id = tracking_ids[i]

        def make_progress(tid: str):
            def cb(jid: str, step: str, detail: str = ""):
                _progress_callback(tid, step, detail)

            return cb

        _jobs[tracking_id]["status"] = "running"

        result = run_pipeline(
            niche=job.niche,
            platforms=job.platforms,
            upload_config=job.upload_config,
            on_progress=make_progress(tracking_id),
        )

        result["tracking_id"] = tracking_id
        _jobs[tracking_id] = result

        logger.info(
            f"Queue job {i + 1}/{len(jobs)} done "
            f"(tracking_id={tracking_id}, status={result.get('status')})"
        )


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/niches")
def get_niches():
    return {"niches": NICHES}


@router.post("/generate")
def generate_video(req: JobRequest, background_tasks: BackgroundTasks):
    tracking_id = str(uuid.uuid4())[:8]
    _jobs[tracking_id] = {"status": "queued", "step": "", "detail": ""}

    background_tasks.add_task(
        _run_single_job,
        tracking_id,
        req.niche,
        req.platforms,
        req.upload_config,
    )

    logger.info(
        f"Job queued: {tracking_id} | niche={req.niche} | platforms={req.platforms}"
    )
    return {"job_id": tracking_id, "status": "queued"}


@router.post("/queue")
def queue_videos(req: QueueRequest, background_tasks: BackgroundTasks):
    tracking_ids = [str(uuid.uuid4())[:8] for _ in req.jobs]

    for tid in tracking_ids:
        _jobs[tid] = {"status": "queued", "step": "", "detail": ""}

    background_tasks.add_task(_run_queue_jobs, req.jobs, tracking_ids)

    logger.info(f"Queue started: {len(tracking_ids)} jobs | IDs: {tracking_ids}")
    return {"job_ids": tracking_ids, "count": len(tracking_ids)}


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.get("/jobs")
def list_jobs():
    return {
        "total": len(_jobs),
        "queued": sum(1 for j in _jobs.values() if j.get("status") == "queued"),
        "running": sum(1 for j in _jobs.values() if j.get("status") == "running"),
        "complete": sum(1 for j in _jobs.values() if j.get("status") == "complete"),
        "failed": sum(1 for j in _jobs.values() if j.get("status") == "failed"),
        "jobs": _jobs,
    }


@router.delete("/jobs")
def clear_jobs():
    count = len(_jobs)
    _jobs.clear()
    logger.info(f"Cleared {count} jobs from store")
    return {"cleared": count}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    del _jobs[job_id]
    return {"deleted": job_id}
