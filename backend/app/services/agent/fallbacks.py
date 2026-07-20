from __future__ import annotations

import re


def extract_research_sentences(source_context: str, limit: int = 6) -> list[str]:
    cleaned = re.sub(r"(?m)^(Research notes|Source context:|User request:.*|Topic:.*)$", "", source_context)
    cleaned = re.sub(r"(?m)^\d+\.\s+.+$", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*(Key detail|Evidence|Snippet|Content):\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    candidates = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences: list[str] = []
    seen: set[str] = set()
    for sentence in candidates:
        normalized = sentence.strip(" -")
        key = normalized.lower()
        if len(normalized) < 45 or key in seen:
            continue
        sentences.append(normalized)
        seen.add(key)
        if len(sentences) >= limit:
            break
    return sentences


def build_response_timeout_fallback(
    source_context: str,
) -> str:
    sentences = extract_research_sentences(source_context)
    if not sentences:
        return "I found some relevant information, but there was not enough clean text to summarize confidently. Try asking the question again in quick mode or with a narrower topic."

    intro = sentences[0]
    key_points = "\n".join(f"- {sentence}" for sentence in sentences[1:6])
    if key_points:
        return f"{intro}\n\nKey points\n{key_points}"
    return intro
