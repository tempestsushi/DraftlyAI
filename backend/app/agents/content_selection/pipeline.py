from __future__ import annotations

from .chunking import chunk_sources
from .dedupe import cluster_duplicates
from .formatter import format_selected_context
from .models import PipelineConfig, SelectedContext
from .scoring import score_chunks
from .selection import select_chunks


class ContentSelectionPipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    def process(self, topic: str, sources: list[dict[str, str]]) -> SelectedContext:
        topic = " ".join(topic.split()).strip()
        if not topic:
            raise ValueError("Topic is required for source selection")
        if not sources:
            return SelectedContext(
                topic,
                [],
                0,
                {},
                [{"chunk_id": "", "reason": "no_sources"}],
                {
                    "candidate_chunks": 0,
                    "scored_chunks": 0,
                    "relevance_threshold": self.config.minimum_relevance,
                    "top_relevance_scores": "none",
                    "fallback_selected": 0,
                    "source_token_budget": self.config.total_source_token_budget,
                    "selected_idea_target": self.config.selected_idea_target,
                },
            )
        if self.config.total_source_token_budget < 80:
            raise ValueError("Source token budget is too small")

        chunks = chunk_sources(topic, sources, self.config)
        if not chunks:
            return SelectedContext(
                topic,
                [],
                0,
                {},
                [{"chunk_id": "", "reason": "no_relevant_chunks"}],
                {
                    "candidate_chunks": 0,
                    "scored_chunks": 0,
                    "relevance_threshold": self.config.minimum_relevance,
                    "top_relevance_scores": "none",
                    "fallback_selected": 0,
                    "source_token_budget": self.config.total_source_token_budget,
                    "selected_idea_target": self.config.selected_idea_target,
                },
            )

        scored = score_chunks(topic, chunks, self.config)
        fallback_selected = 0
        if not scored:
            scored = self._fallback_chunks(chunks)
            fallback_selected = len(scored)
        low_relevance = [
            {"chunk_id": chunk.chunk_id, "reason": "low_relevance"}
            for chunk in chunks
            if chunk not in scored
        ]
        representatives, support, duplicate_exclusions = cluster_duplicates(scored, self.config)
        selected_context = select_chunks(
            topic,
            representatives,
            support,
            [*low_relevance, *duplicate_exclusions],
            self.config,
        )
        selected_context.debug_metrics = {
            "candidate_chunks": len(chunks),
            "scored_chunks": len(scored),
            "relevance_threshold": self.config.minimum_relevance,
            "top_relevance_scores": _format_top_relevance_scores(chunks),
            "fallback_selected": fallback_selected,
            "source_token_budget": self.config.total_source_token_budget,
            "selected_idea_target": self.config.selected_idea_target,
        }
        return selected_context

    def _fallback_chunks(self, chunks: list) -> list:
        candidates = [
            chunk
            for chunk in chunks
            if chunk.relevance_score >= self.config.fallback_minimum_relevance
            or chunk.title_relevance_score > 0
        ]
        if not candidates:
            candidates = list(chunks)
        selected = sorted(
            candidates,
            key=lambda chunk: (chunk.candidate_score, chunk.title_relevance_score, chunk.specificity_score),
            reverse=True,
        )[: self.config.fallback_chunk_count]
        for chunk in selected:
            chunk.selected_by_fallback = True
        return selected


def _format_top_relevance_scores(chunks: list) -> str:
    scores = sorted((chunk.relevance_score for chunk in chunks), reverse=True)[:5]
    if not scores:
        return "none"
    return ", ".join(f"{score:.2f}" for score in scores)


def select_source_context(
    topic: str,
    sources: list[dict[str, str]],
    *,
    total_source_token_budget: int,
    maximum_chunks_per_source: int = 2,
) -> str:
    pipeline = ContentSelectionPipeline(
        PipelineConfig(
            total_source_token_budget=total_source_token_budget,
            maximum_chunks_per_source=maximum_chunks_per_source,
        )
    )
    return format_selected_context(pipeline.process(topic, sources))
