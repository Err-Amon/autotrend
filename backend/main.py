from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import validate_env
from utils.file_manager import ensure_storage_dirs
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoTrend Video Factory API starting up")

    ensure_storage_dirs()
    logger.info("Storage directories ready")

    missing = validate_env()
    if missing:
        logger.warning(
            f"Missing required .env keys: {missing} — "
            f"pipeline will fail until these are set"
        )
    else:
        logger.info("Environment validated — all required keys present")

    yield

    logger.info("AutoTrend Video Factory API shutting down")


app = FastAPI(
    title="AutoTrend Video Factory API",
    version="1.0.0",
    description="Automated short-form video creation and upload pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
