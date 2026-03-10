from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import validate_env
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="AutoTrend Video Factory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def on_startup():
    missing = validate_env()
    if missing:
        logger.warning(f"Missing required env keys: {missing}. Pipeline will fail until these are set.")
    else:
        logger.info("Environment validated. All required keys present.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
