from __future__ import annotations

import re
from difflib import SequenceMatcher

try:
    from nltk.stem import PorterStemmer
except ImportError:  # pragma: no cover - only used before dependencies are installed
    PorterStemmer = None

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - only used before dependencies are installed
    fuzz = None

STOPWORDS = {
    "about",
    "also",
    "and",
    "are",
    "because",
    "been",
    "being",
    "can",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "its",
    "learn",
    "like",
    "make",
    "more",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "through",
    "today",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "why",
    "world",
    "would",
}

_STEMMER = PorterStemmer() if PorterStemmer is not None else None


def estimate_tokens(text: str) -> int:
    return max(1, round(len(re.findall(r"\S+", text)) / 0.75))


def sentence_split(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
        if len(sentence.strip()) >= 20
    ]


def terms_for_text(text: str) -> set[str]:
    terms: set[str] = set()
    for term in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text.lower()):
        if term in STOPWORDS:
            continue
        normalized = normalize_term(term)
        terms.add(normalized)
    return terms


def normalize_term(term: str) -> str:
    cleaned = term.lower().strip(".,:;!?()[]{}\"'")
    if _STEMMER is not None:
        return _STEMMER.stem(cleaned)
    for suffix in ("ing", "ers", "er", "es", "s"):
        if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 3:
            return cleaned[: -len(suffix)]
    return cleaned


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def lexical_similarity(left: set[str], right: set[str]) -> float:
    exact_score = jaccard_similarity(left, right)
    if not left or not right:
        return exact_score

    fuzzy_matches = 0
    for left_term in left:
        best_score = max(_term_similarity(left_term, right_term) for right_term in right)
        if best_score >= 0.86:
            fuzzy_matches += 1
    fuzzy_score = fuzzy_matches / max(len(left), len(right), 1)
    return max(exact_score, fuzzy_score)


def _term_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if fuzz is not None:
        return fuzz.ratio(left, right) / 100
    return SequenceMatcher(None, left, right).ratio()


def normalized_text_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
