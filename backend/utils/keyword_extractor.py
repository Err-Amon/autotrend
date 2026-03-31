import re
from integrations.groq_client import groq_chat
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


def extract_keywords_with_groq(script: str, max_keywords: int = 5) -> list[str]:
    if not script:
        return []

    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Extract {max_keywords} key visual keywords from this video script for stock video search. "
                    f"Focus on nouns, objects, scenes, actions that can be depicted in videos. "
                    f"Keywords should be relevant to finding matching video clips. "
                    f"Output only comma-separated keywords, no explanations or extra text.\n\nScript: {script}"
                ),
            }
        ]
        response = groq_chat(messages, max_tokens=100)
        if response:
            keywords = [k.strip().lower() for k in response.split(",") if k.strip()]
            keywords = keywords[:max_keywords]
            logger.info(f"Groq extracted keywords: {keywords}")
            return keywords
        else:
            logger.warning("Groq keyword extraction returned empty, falling back")
            return extract_keywords(script, max_keywords)
    except Exception as e:
        logger.error(f"Groq keyword extraction failed: {e}, falling back")
        return extract_keywords(script, max_keywords)


def keywords_to_query(keywords: list[str], max_words: int = 3) -> str:
    return " ".join(keywords[:max_words])


def get_visual_description(segment: str) -> str:
    if not segment:
        return "nature"

    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Describe a visual scene that matches this script segment for stock video search. "
                    f"Provide a short phrase (1-5 words) describing what should be shown in the video. "
                    f"Focus on visual elements like objects, actions, or settings. "
                    f"Output only the description phrase, no extra text.\n\nSegment: {segment}"
                ),
            }
        ]
        response = groq_chat(messages, max_tokens=50)
        if response:
            description = response.strip()
            logger.info(f"Visual description: '{description}' for segment: '{segment}'")
            return description
        else:
            logger.warning("Groq visual description returned empty, using segment")
            return segment[:50]  # fallback
    except Exception as e:
        logger.error(f"Groq visual description failed: {e}, using segment")
        return segment[:50]
