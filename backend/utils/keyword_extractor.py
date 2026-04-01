import re
from integrations.gemini_client import gemini_chat
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
                "role": "system",
                "content": (
                    "You are a video production expert specializing in stock footage selection. "
                    "Your task is to analyze a video script and generate highly specific, visual search queries "
                    "that will find stock video clips that perfectly match the script's content.\n\n"
                    "CRITICAL RULES:\n"
                    "1. Focus on VISUAL elements only - what can be seen on screen\n"
                    "2. Each query must be 1-3 words, concrete nouns or actions\n"
                    "3. Prioritize specific objects, activities, settings, and movements\n"
                    "4. AVOID generic terms: people, person, man, woman, background, abstract, concept, nature, city\n"
                    "5. AVOID vague adjectives: beautiful, amazing, good, bad, nice\n"
                    "6. Think: 'What would I actually see in a video of this topic?'\n"
                    "7. Output ONLY comma-separated queries, no explanations"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyze this script and return exactly {max_keywords} highly specific stock-video search queries "
                    f"that visually represent the main subject matter. Focus on concrete visual elements.\n\n"
                    f"Script:\n{script}"
                ),
            },
        ]
        response = gemini_chat(messages, max_tokens=120)
        if response:
            keywords = [k.strip().lower() for k in response.split(",") if k.strip()]
            # Discard any item that looks like a sentence (more than 4 words)
            keywords = [k for k in keywords if len(k.split()) <= 4]
            # Filter out generic terms that often lead to irrelevant clips
            generic_terms = {
                "people",
                "person",
                "man",
                "woman",
                "background",
                "abstract",
                "concept",
                "nature",
                "city",
                "video",
                "footage",
                "clip",
            }
            keywords = [k for k in keywords if not any(g in k for g in generic_terms)]
            keywords = keywords[:max_keywords]
            logger.info(f"Groq extracted visual queries: {keywords}")
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
                "role": "system",
                "content": (
                    "You are a stock footage expert. Given a script segment, describe the most relevant "
                    "visual scene that would perfectly illustrate this content. "
                    "Focus on concrete, searchable visual elements - objects, actions, settings, movements. "
                    "Avoid generic terms like 'people', 'person', 'nature', 'city'. "
                    "Output only 1-5 words describing the visual scene."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"What specific visual scene would best illustrate this script segment? "
                    f"Think: 'What would I see on screen?'\n\nSegment: {segment}"
                ),
            },
        ]
        response = gemini_chat(messages, max_tokens=50)
        if response:
            description = response.strip()
            # Filter out generic terms
            generic_terms = {
                "people",
                "person",
                "man",
                "woman",
                "nature",
                "city",
                "background",
            }
            if not any(g in description.lower() for g in generic_terms):
                logger.info(
                    f"Visual description: '{description}' for segment: '{segment}'"
                )
                return description
            else:
                logger.warning(
                    "Visual description contains generic terms, using segment"
                )
                return segment[:50]
        else:
            logger.warning("Groq visual description returned empty, using segment")
            return segment[:50]  # fallback
    except Exception as e:
        logger.error(f"Groq visual description failed: {e}, using segment")
        return segment[:50]
