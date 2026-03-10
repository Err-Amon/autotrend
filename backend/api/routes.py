from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from pipelines.video_pipeline import run_pipeline, run_queue
from config import NICHES
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

job_status: dict = {}

class JobRequest(BaseModel):
    niche: str
    platforms: list[str] = []
    upload_config: dict = {}

class QueueRequest(BaseModel):
    jobs: list[JobRequest]

def _run_job(job_id: str, niche: str, platforms: list[str], upload_config: dict):
    def on_progress(jid, step):
        if jid in job_status:
            job_status[jid]["step"] = step

    job_status[job_id] = {"status": "running", "step": "starting"}
    result = run_pipeline(niche, platforms, upload_config, on_progress=on_progress)
    job_status[job_id] = result

@router.get("/niches")
def get_niches():
    return {"niches": NICHES}

@router.post("/generate")
def generate_video(req: JobRequest, background_tasks: BackgroundTasks):
    import uuid
    job_id = str(uuid.uuid4())[:8]
    job_status[job_id] = {"status": "queued"}
    background_tasks.add_task(_run_job, job_id, req.niche, req.platforms, req.upload_config)
    return {"job_id": job_id, "status": "queued"}

@router.post("/queue")
def queue_videos(req: QueueRequest, background_tasks: BackgroundTasks):
    import uuid
    ids = []
    for job in req.jobs:
        job_id = str(uuid.uuid4())[:8]
        job_status[job_id] = {"status": "queued"}
        ids.append(job_id)
    background_tasks.add_task(_process_queue, req.jobs, ids)
    return {"job_ids": ids}

def _process_queue(jobs, ids):
    for i, job in enumerate(jobs):
        job_id = ids[i]
        _run_job(job_id, job.niche, job.platforms, job.upload_config)

@router.get("/status/{job_id}")
def get_status(job_id: str):
    return job_status.get(job_id, {"status": "not_found"})

@router.get("/jobs")
def list_jobs():
    return {"jobs": job_status}
