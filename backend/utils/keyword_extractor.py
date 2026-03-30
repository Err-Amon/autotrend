import re
from utils.logger import get_logger

logger = get_logger(__name__)

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "it",
    "its",
    "this",
    "that",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "not",
    "no",
    "so",
    "if",
    "as",
    "up",
    "out",
    "about",
    "into",
    "than",
    "then",
    "they",
    "them",
    "their",
    "we",
    "our",
    "you",
    "your",
    "he",
    "she",
    "his",
    "her",
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "just",
    "also",
    "more",
    "most",
    "very",
    "too",
    "even",
    "now",
    "only",
    "after",
    "before",
    "over",
    "while",
    "during",
    "through",
    "each",
    "which",
    "there",
    "here",
    "time",
    "way",
    "like",
    "make",
    "know",
    "take",
    "come",
    "see",
    "get",
    "give",
    "think",
    "look",
    "want",
    "back",
}


def extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    if not text:
        return []

    try:
        # Extract words of 4+ chars
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
        words = [w.lower() for w in words if w.lower() not in STOPWORDS]

        # Count frequency
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency then alphabetically for determinism
        sorted_words = sorted(freq.keys(), key=lambda w: (-freq[w], w))
        keywords = sorted_words[:max_keywords]

        logger.info(f"Extracted keywords: {keywords}")
        return keywords

    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []


def keywords_to_query(keywords: list[str], max_words: int = 3) -> str:
    return " ".join(keywords[:max_words])
