import time
from utils.logger import get_logger

logger = get_logger(__name__)

def retry(func, retries: int = 3, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    logger.error(f"All {retries} attempts failed for {func.__name__}")
    return None
