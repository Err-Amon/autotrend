import time
from utils.logger import get_logger

logger = get_logger(__name__)


def retry(func, retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    func_name = getattr(func, "__name__", repr(func))
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            wait = delay * (backoff ** (attempt - 1))
            logger.warning(
                f"[{func_name}] Attempt {attempt}/{retries} failed: {e}. Retrying in {wait:.1f}s"
            )
            if attempt < retries:
                time.sleep(wait)
    logger.error(
        f"[{func_name}] All {retries} attempts failed. Last error: {last_error}"
    )
    return None
