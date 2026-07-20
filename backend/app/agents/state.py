from __future__ import annotations

from typing import TypedDict

from ..models import ResearchDepth


class AgentState(TypedDict, total=False):
    topic_id: str
    topic: str
    research_depth: ResearchDepth
    conversation_summary: str
    recent_messages: list[dict[str, str]]
    prior_sources: list[dict[str, str]]
    plan: str
    planner_warning: str
    search_query: str
    search_queries: list[str]
    search_results: list[dict[str, str]]
    fetched_sources: list[dict[str, str]]
    source_context: str
    evidence_mode: str
    evidence_error: str
    content_selection_debug_log: str
    draft: str
