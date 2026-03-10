import re
from utils.logger import get_logger

logger = get_logger(__name__)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "it", "its", "this", "that", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "not", "no", "so", "if", "as", "up", "out", "about", "into", "than",
}

def extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    try:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
        words = [w.lower() for w in words if w.lower() not in STOPWORDS]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        return sorted_words[:max_keywords]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []
