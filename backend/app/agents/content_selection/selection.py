from __future__ import annotations

from collections import Counter

from .mmr import calculate_mmr
from .models import PipelineConfig, SelectedContext, SelectedItem, SourceChunk


def select_chunks(
    topic: str,
    candidates: list[SourceChunk],
    support: dict[str, list[str]],
    excluded_chunks: list[dict[str, str]],
    config: PipelineConfig,
) -> SelectedContext:
    selected: list[SourceChunk] = []
    coverage: Counter[str] = Counter()
    used_tokens = 0
    remaining = list(candidates)
    selected_idea_target = max(1, config.selected_idea_target)

    for source_id in _source_order(remaining):
        if len(selected) >= selected_idea_target:
            break
        source_candidates = [chunk for chunk in remaining if chunk.source_id == source_id]
        if not source_candidates:
            continue
        best = max(source_candidates, key=lambda item: item.candidate_score)
        if used_tokens + best.token_count > config.total_source_token_budget:
            excluded_chunks.append({"chunk_id": best.chunk_id, "reason": "token_budget"})
            continue
        selected.append(best)
        coverage[best.source_id] += 1
        used_tokens += best.token_count
        remaining.remove(best)

    while remaining and len(selected) < selected_idea_target:
        allowed = [
            chunk
            for chunk in remaining
            if coverage[chunk.source_id] < config.maximum_chunks_per_source
        ]
        if not allowed:
            break
        best = max(allowed, key=lambda item: calculate_mmr(item, selected, config))
        mmr_score = calculate_mmr(best, selected, config)
        if used_tokens + best.token_count > config.total_source_token_budget:
            excluded_chunks.append({"chunk_id": best.chunk_id, "reason": "token_budget"})
            remaining.remove(best)
            continue
        best.candidate_score = mmr_score
        selected.append(best)
        coverage[best.source_id] += 1
        used_tokens += best.token_count
        remaining.remove(best)

    selected_items = [
        SelectedItem(
            text=chunk.text,
            primary_source_id=chunk.source_id,
            supporting_source_ids=support.get(chunk.chunk_id, [chunk.source_id]),
            source_title=chunk.source_title,
            source_url=chunk.source_url,
            token_count=chunk.token_count,
            relevance_score=chunk.relevance_score,
            specificity_score=chunk.specificity_score,
            mmr_score=chunk.candidate_score,
        )
        for chunk in selected
    ]

    return SelectedContext(
        topic=topic,
        selected_items=selected_items,
        total_selected_tokens=used_tokens,
        source_coverage=dict(coverage),
        excluded_chunks=excluded_chunks,
    )


def _source_order(chunks: list[SourceChunk]) -> list[str]:
    best_by_source: dict[str, float] = {}
    for chunk in chunks:
        best_by_source[chunk.source_id] = max(best_by_source.get(chunk.source_id, 0.0), chunk.candidate_score)
    return [
        source_id
        for source_id, _score in sorted(best_by_source.items(), key=lambda item: item[1], reverse=True)
    ]
