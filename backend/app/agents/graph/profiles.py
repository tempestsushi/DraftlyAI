from __future__ import annotations

from dataclasses import dataclass

from ...config import settings
from ...models import ResearchDepth


@dataclass(slots=True)
class ResearchProfile:
    search_max_results: int
    fetch_max_sources: int
    extract_char_limit: int
    source_context_token_budget: int
    gemini_output_tokens: int
    min_thinking_seconds: int
    max_thinking_seconds: int
    search_query_count: int
    answer_word_target: int
    answer_guidance: str
    source_context_idea_target: int
    rag_top_k: int
    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_source_char_limit: int
    fetch_enabled: bool = True


def resolve_research_profile(depth: ResearchDepth) -> ResearchProfile:
    if depth == ResearchDepth.quick:
        return ResearchProfile(
            search_max_results=3,
            fetch_max_sources=1,
            extract_char_limit=1000,
            source_context_token_budget=300,
            gemini_output_tokens=700,
            min_thinking_seconds=0,
            max_thinking_seconds=45,
            search_query_count=1,
            answer_word_target=200,
            answer_guidance="Keep it concise. Use one source/snippet and answer directly.",
            source_context_idea_target=1,
            rag_top_k=settings.rag_quick_top_k,
            rag_chunk_size=settings.rag_quick_chunk_size,
            rag_chunk_overlap=settings.rag_quick_chunk_overlap,
            rag_source_char_limit=settings.rag_quick_source_char_limit,
            fetch_enabled=False,
        )
    if depth == ResearchDepth.moderate:
        return ResearchProfile(
            search_max_results=4,
            fetch_max_sources=2,
            extract_char_limit=1200,
            source_context_token_budget=600,
            gemini_output_tokens=1100,
            min_thinking_seconds=0,
            max_thinking_seconds=75,
            search_query_count=2,
            answer_word_target=350,
            answer_guidance="Give a fuller explanation with examples or practical use cases.",
            source_context_idea_target=3,
            rag_top_k=settings.rag_moderate_top_k,
            rag_chunk_size=settings.rag_moderate_chunk_size,
            rag_chunk_overlap=settings.rag_moderate_chunk_overlap,
            rag_source_char_limit=settings.rag_moderate_source_char_limit,
            fetch_enabled=True,
        )
    if depth == ResearchDepth.deep:
        return ResearchProfile(
            search_max_results=4,
            fetch_max_sources=4,
            extract_char_limit=2000,
            source_context_token_budget=900,
            gemini_output_tokens=1600,
            min_thinking_seconds=0,
            max_thinking_seconds=120,
            search_query_count=3,
            answer_word_target=500,
            answer_guidance="Synthesize deeply. Include tradeoffs, comparisons, practical steps, and clear structure.",
            source_context_idea_target=5,
            rag_top_k=settings.rag_deep_top_k,
            rag_chunk_size=settings.rag_deep_chunk_size,
            rag_chunk_overlap=settings.rag_deep_chunk_overlap,
            rag_source_char_limit=settings.rag_deep_source_char_limit,
            fetch_enabled=True,
        )
    return ResearchProfile(
        search_max_results=settings.web_search_max_results,
        fetch_max_sources=settings.web_fetch_max_sources,
        extract_char_limit=settings.web_extract_char_limit,
        source_context_token_budget=900,
        gemini_output_tokens=settings.gemini_max_output_tokens,
        min_thinking_seconds=0,
        max_thinking_seconds=75,
        search_query_count=2,
        answer_word_target=350,
        answer_guidance="Give a clear answer with examples or practical use cases.",
        source_context_idea_target=3,
        rag_top_k=settings.rag_top_k,
        rag_chunk_size=settings.rag_chunk_size,
        rag_chunk_overlap=settings.rag_chunk_overlap,
        rag_source_char_limit=settings.rag_source_char_limit,
    )
