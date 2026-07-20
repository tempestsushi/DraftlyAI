from __future__ import annotations

from .models import PipelineConfig, SourceChunk
from .text import lexical_similarity


def calculate_mmr(
    candidate: SourceChunk,
    selected: list[SourceChunk],
    config: PipelineConfig,
) -> float:
    if not selected:
        return candidate.candidate_score
    max_similarity = max(lexical_similarity(candidate.terms, item.terms) for item in selected)
    return (config.mmr_lambda * candidate.candidate_score) - ((1 - config.mmr_lambda) * max_similarity)
