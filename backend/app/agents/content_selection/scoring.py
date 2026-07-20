from __future__ import annotations

import re

from .models import PipelineConfig, SourceChunk
from .text import lexical_similarity, terms_for_text


SPECIFICITY_PATTERNS = (
    r"\b\d+(?:\.\d+)?%?\b",
    r"\b20\d{2}\b",
    r"\$[\d,.]+",
    r"\b(?:example|case study|study|report|survey|research|data|according to)\b",
    r"\b(?:because|therefore|results in|leads to|helps|enables|reduces|increases|improves)\b",
    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b",
)


def score_chunks(topic: str, chunks: list[SourceChunk], config: PipelineConfig) -> list[SourceChunk]:
    topic_terms = terms_for_text(topic)
    scored: list[SourceChunk] = []
    for chunk in chunks:
        content_terms = terms_for_text(chunk.text)
        title_terms = terms_for_text(chunk.source_title)
        content_relevance = lexical_similarity(topic_terms, content_terms)
        title_relevance = lexical_similarity(topic_terms, title_terms)
        relevance = min(1.0, content_relevance + (title_relevance * config.title_relevance_boost))
        specificity = calculate_specificity(chunk.text)
        chunk.relevance_score = relevance
        chunk.title_relevance_score = title_relevance
        chunk.specificity_score = specificity
        chunk.candidate_score = (
            config.relevance_weight * relevance
            + config.specificity_weight * specificity
        )
        if relevance >= config.minimum_relevance:
            scored.append(chunk)
    return sorted(scored, key=lambda item: item.candidate_score, reverse=True)


def calculate_specificity(text: str) -> float:
    if not text.strip():
        return 0.0
    hits = 0
    for pattern in SPECIFICITY_PATTERNS:
        hits += min(3, len(re.findall(pattern, text, flags=re.I)))
    length_bonus = min(len(text.split()) / 120, 1.0)
    return min(1.0, (hits / 12) + (0.15 * length_bonus))
