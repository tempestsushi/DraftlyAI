from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PipelineConfig:
    target_chunk_tokens: int = 90
    chunk_overlap_sentences: int = 1
    minimum_relevance: float = 0.05
    duplicate_similarity_threshold: float = 0.72
    mmr_lambda: float = 0.72
    total_source_token_budget: int = 500
    selected_idea_target: int = 3
    minimum_chunks_per_source: int = 1
    maximum_chunks_per_source: int = 2
    relevance_weight: float = 0.75
    specificity_weight: float = 0.25
    title_relevance_boost: float = 0.08
    fallback_minimum_relevance: float = 0.02
    fallback_chunk_count: int = 2


@dataclass(slots=True)
class SourceChunk:
    chunk_id: str
    source_id: str
    source_title: str
    source_url: str
    text: str
    token_count: int
    terms: set[str] = field(default_factory=set)
    relevance_score: float = 0.0
    specificity_score: float = 0.0
    candidate_score: float = 0.0
    title_relevance_score: float = 0.0
    selected_by_fallback: bool = False


@dataclass(slots=True)
class SelectedItem:
    text: str
    primary_source_id: str
    supporting_source_ids: list[str]
    source_title: str
    source_url: str
    token_count: int
    relevance_score: float
    specificity_score: float
    mmr_score: float


@dataclass(slots=True)
class SelectedContext:
    topic: str
    selected_items: list[SelectedItem]
    total_selected_tokens: int
    source_coverage: dict[str, int]
    excluded_chunks: list[dict[str, str]]
    debug_metrics: dict[str, str | int | float] = field(default_factory=dict)
