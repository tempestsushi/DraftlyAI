from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from textwrap import dedent

from langchain_core.messages import HumanMessage, SystemMessage

from ...config import settings
from ...models import DraftLength, DraftTone
from ..content_selection import ContentSelectionPipeline, PipelineConfig, SelectedContext, format_selected_context
from ..retrieval.models import RagConfig, RagContext
from ..retrieval.pipeline import build_rag_source_context, format_rag_context
from ..prompts import (
    ANSWER_SYSTEM_PROMPT,
    CONVERSATION_SUMMARY_SYSTEM_PROMPT,
    DRAFT_COMPLETION_SYSTEM_PROMPT,
    DRAFT_FROM_ANSWER_SYSTEM_PROMPT,
    DRAFT_SYSTEM_PROMPT,
    PLAN_SYSTEM_PROMPT,
    REWRITE_SYSTEM_PROMPT,
)
from .profiles import ResearchProfile
from .ranking import build_search_query_variants, rank_search_results


@dataclass(slots=True)
class AgentGraph:
    llm: object
    graph: object
    research_profile: ResearchProfile | None = None
    last_usage_metadata: dict | None = None
    last_content_selection_debug_log: str = ""
    last_draft_repair_performed: bool = False

    rank_search_results = staticmethod(rank_search_results)
    build_search_query_variants = staticmethod(build_search_query_variants)

    def _timeout_with_depth(self, base_seconds: float) -> float:
        return base_seconds

    async def _ainvoke_text(self, messages: list, *, timeout_seconds: float) -> str:
        result = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=timeout_seconds)
        usage = getattr(result, "usage_metadata", None)
        if isinstance(usage, dict):
            self.last_usage_metadata = usage
        return result.content if isinstance(result.content, str) else str(result.content)

    async def _stream_text(self, messages: list, *, chunk_timeout_seconds: float):
        self.last_usage_metadata = None
        stream = self.llm.astream(messages)
        while True:
            try:
                chunk = await asyncio.wait_for(anext(stream), timeout=chunk_timeout_seconds)
            except StopAsyncIteration:
                break
            usage = getattr(chunk, "usage_metadata", None)
            if isinstance(usage, dict):
                self.last_usage_metadata = usage
            text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            if text:
                yield text

    def consume_usage_metadata(self) -> dict | None:
        usage = self.last_usage_metadata
        self.last_usage_metadata = None
        return usage

    def consume_content_selection_debug_log(self) -> str:
        debug_log = self.last_content_selection_debug_log
        self.last_content_selection_debug_log = ""
        return debug_log

    def _response_chunk_timeout(self) -> float:
        if self.research_profile is None:
            return settings.agent_response_chunk_timeout_seconds
        return max(settings.agent_response_chunk_timeout_seconds, float(self.research_profile.max_thinking_seconds))

    @staticmethod
    def _format_recent_messages(recent_messages: list[dict[str, str]]) -> str:
        if not recent_messages:
            return ""
        lines: list[str] = []
        recent_limit = min(settings.chat_recent_messages_limit, 3)
        for message in recent_messages[-recent_limit:]:
            role = message.get("role", "unknown").capitalize()
            content = message.get("content", "").strip()
            if content:
                limit = settings.chat_message_context_char_limit
                if role.lower() == "assistant":
                    limit = max(120, limit // 2)
                if len(content) > limit:
                    content = f"{content[:limit].rstrip()}..."
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _conversation_context_block(
        self,
        conversation_summary: str,
        recent_messages: list[dict[str, str]],
    ) -> str:
        summary = conversation_summary.strip()
        if len(summary) > settings.chat_summary_char_limit:
            summary = f"{summary[:settings.chat_summary_char_limit].rstrip()}..."
        messages_block = self._format_recent_messages(recent_messages)
        parts: list[str] = []
        if summary:
            parts.append(f"Conversation summary:\n{summary}")
        if messages_block:
            parts.append(f"Recent messages:\n{messages_block}")
        return "\n\n".join(parts) + ("\n\n" if parts else "")

    def _depth_response_guidance(self) -> str:
        if self.research_profile is None:
            return "Target about 350 words. Give a clear answer with practical detail."
        return (
            f"Target about {self.research_profile.answer_word_target} words. "
            f"{self.research_profile.answer_guidance}"
        )

    @staticmethod
    def _style_guidance(response_style: str = "") -> str:
        response_style = " ".join(response_style.split())[:180]
        return f"\nStyle preference: {response_style}\n" if response_style else ""

    @staticmethod
    def build_extractive_source_context(
        topic: str,
        fetched_sources: list[dict[str, str]],
        *,
        source_context_token_budget: int = 650,
        sentences_per_source: int = 3,
        selected_idea_target: int = 3,
    ) -> SelectedContext:
        if not fetched_sources:
            return SelectedContext(
                topic,
                [],
                0,
                {},
                [{"chunk_id": "", "reason": "no_sources"}],
            )
        source_count = max(1, len(fetched_sources))
        token_budget = max(180, source_context_token_budget)
        max_chunks_per_source = (
            1
            if source_count <= selected_idea_target
            else max(1, min(2, sentences_per_source))
        )
        pipeline = ContentSelectionPipeline(
            PipelineConfig(
                target_chunk_tokens=max(60, min(120, token_budget // source_count)),
                minimum_relevance=0.05,
                duplicate_similarity_threshold=0.7,
                total_source_token_budget=token_budget,
                selected_idea_target=selected_idea_target,
                maximum_chunks_per_source=max_chunks_per_source,
            )
        )
        return pipeline.process(topic, fetched_sources)

    @classmethod
    def build_extractive_source_context_text(
        cls,
        topic: str,
        fetched_sources: list[dict[str, str]],
        *,
        source_context_token_budget: int = 650,
        sentences_per_source: int = 3,
        selected_idea_target: int = 3,
    ) -> str:
        context = cls.build_extractive_source_context(
            topic,
            fetched_sources,
            source_context_token_budget=source_context_token_budget,
            sentences_per_source=sentences_per_source,
            selected_idea_target=selected_idea_target,
        )
        return format_selected_context(context)

    @staticmethod
    def format_content_selection_debug_log(context: SelectedContext, *, source_count: int) -> str:
        excluded_counts: dict[str, int] = {}
        for item in context.excluded_chunks:
            reason = item.get("reason", "unknown")
            excluded_counts[reason] = excluded_counts.get(reason, 0) + 1

        coverage = ", ".join(
            f"{source_id}:{count}" for source_id, count in sorted(context.source_coverage.items())
        ) or "none"
        exclusions = ", ".join(
            f"{reason}:{count}" for reason, count in sorted(excluded_counts.items())
        ) or "none"
        selected = len(context.selected_items)
        avg_relevance = (
            sum(item.relevance_score for item in context.selected_items) / selected
            if selected
            else 0
        )
        avg_specificity = (
            sum(item.specificity_score for item in context.selected_items) / selected
            if selected
            else 0
        )
        return (
            "Content selection stats:\n"
            f"- fetched sources: {source_count}\n"
            f"- candidate chunks: {context.debug_metrics.get('candidate_chunks', 0)}\n"
            f"- scored chunks: {context.debug_metrics.get('scored_chunks', 0)}\n"
            f"- relevance threshold: {float(context.debug_metrics.get('relevance_threshold', 0)):.2f}\n"
            f"- top relevance scores: {context.debug_metrics.get('top_relevance_scores', 'none')}\n"
            f"- fallback selected: {context.debug_metrics.get('fallback_selected', 0)}\n"
            f"- source token budget: {context.debug_metrics.get('source_token_budget', 0)}\n"
            f"- selected idea target: {context.debug_metrics.get('selected_idea_target', selected)}\n"
            f"- selected ideas: {selected}\n"
            f"- selected source tokens: {context.total_selected_tokens}\n"
            f"- source coverage: {coverage}\n"
            f"- excluded chunks: {exclusions}\n"
            f"- avg relevance: {avg_relevance:.2f}\n"
            f"- avg specificity: {avg_specificity:.2f}"
        )

    @staticmethod
    def format_rag_debug_log(context: RagContext, *, source_count: int) -> str:
        metrics = context.debug_metrics
        return (
            "RAG retrieval stats:\n"
            f"- fetched sources: {source_count}\n"
            f"- provider: {metrics.get('rag_provider', 'local')}\n"
            f"- embed model: {metrics.get('rag_embed_model', '') or 'not used'}\n"
            f"- retrieval mode: {metrics.get('rag_retrieval_mode', 'lexical_fallback')}\n"
            f"- embedding error: {metrics.get('rag_embedding_error', '') or 'none'}\n"
            f"- top k: {metrics.get('rag_top_k', 0)}\n"
            f"- chunk size: {metrics.get('rag_chunk_size', 0)}\n"
            f"- chunk overlap: {metrics.get('rag_chunk_overlap', 0)}\n"
            f"- source char limit: {metrics.get('rag_source_char_limit', 0)}\n"
            f"- candidate chunks: {metrics.get('rag_candidate_chunks', 0)}\n"
            f"- selected chunks: {metrics.get('rag_selected_chunks', 0)}\n"
            f"- selected chars: {metrics.get('rag_selected_chars', 0)}\n"
            f"- top scores: {metrics.get('rag_top_scores', 'none')}\n"
            f"- top embedding scores: {metrics.get('rag_top_embedding_scores', 'none')}\n"
            f"- source coverage: {metrics.get('rag_source_coverage', 'none')}"
        )

    @staticmethod
    def is_source_content_usable(source: dict[str, str]) -> bool:
        content = " ".join((source.get("content") or "").split())
        snippet = " ".join((source.get("snippet") or "").split())
        combined = f"{snippet} {content}".strip()
        if len(combined) < 140:
            return False
        if len(combined.split()) < 18:
            return False
        return True

    async def build_plan(self, topic: str) -> str:
        return await self._ainvoke_text(
            [
                SystemMessage(content=PLAN_SYSTEM_PROMPT),
                HumanMessage(content=f"Topic: {topic}"),
            ],
            timeout_seconds=self._timeout_with_depth(settings.agent_plan_timeout_seconds),
        )

    async def build_response(self, topic: str, plan: str) -> str:
        return await self.build_grounded_response(topic, plan, "")

    async def summarize_sources(self, topic: str, fetched_sources: list[dict[str, str]]) -> str:
        if settings.rag_enabled:
            profile = self.research_profile
            config = RagConfig(
                top_k=profile.rag_top_k if profile else settings.rag_top_k,
                chunk_size=profile.rag_chunk_size if profile else settings.rag_chunk_size,
                chunk_overlap=profile.rag_chunk_overlap if profile else settings.rag_chunk_overlap,
                source_char_limit=profile.rag_source_char_limit if profile else settings.rag_source_char_limit,
                provider=settings.rag_provider,
                embed_model=settings.rag_embed_model,
                ollama_base_url=settings.ollama_base_url,
                embedding_timeout_seconds=settings.rag_embedding_timeout_seconds,
            )
            context = build_rag_source_context(topic, fetched_sources, config)
            self.last_content_selection_debug_log = self.format_rag_debug_log(
                context,
                source_count=len(fetched_sources),
            )
            return format_rag_context(context, source_char_limit=config.source_char_limit)

        source_context_token_budget = self.research_profile.source_context_token_budget if self.research_profile else 650
        if source_context_token_budget <= 600:
            sentence_limit = 2
        elif source_context_token_budget <= 900:
            sentence_limit = 3
        else:
            sentence_limit = 4
        context = self.build_extractive_source_context(
            topic,
            fetched_sources,
            source_context_token_budget=source_context_token_budget,
            sentences_per_source=sentence_limit,
            selected_idea_target=self.research_profile.source_context_idea_target if self.research_profile else 3,
        )
        self.last_content_selection_debug_log = self.format_content_selection_debug_log(
            context,
            source_count=len(fetched_sources),
        )
        return format_selected_context(context)

    async def build_grounded_response(
        self,
        topic: str,
        plan: str,
        source_context: str,
        *,
        conversation_summary: str = "",
        recent_messages: list[dict[str, str]] | None = None,
        response_style: str = "",
    ) -> str:
        context_block = self._conversation_context_block(conversation_summary, recent_messages or [])
        return await self._ainvoke_text(
            [
                SystemMessage(content=ANSWER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        context_block
                        + (
                            f"Topic: {topic}\n\n"
                            f"Working plan:\n{plan}\n\n"
                            f"Research context:\n{source_context}\n\n"
                            f"Response guidance:\n{self._depth_response_guidance()}\n\n"
                            f"{self._style_guidance(response_style)}"
                            "Answer the user's request clearly and conversationally. Stay tightly aligned to the user's exact ask."
                        )
                    )
                ),
            ],
            timeout_seconds=self._timeout_with_depth(settings.agent_plan_timeout_seconds),
        )

    async def build_draft_from_answer(self, topic: str, answer: str) -> str:
        return await self.build_draft_from_answer_with_options(
            topic,
            answer,
            tone=DraftTone.professional,
            length=DraftLength.medium,
            include_cta=True,
            include_hashtags=True,
        )

    async def build_draft_from_answer_with_options(
        self,
        topic: str,
        answer: str,
        *,
        tone: DraftTone,
        length: DraftLength,
        include_cta: bool,
        include_hashtags: bool,
    ) -> str:
        answer_notes = self._compact_answer_for_draft(answer, length=length)
        option_block = dedent(
            f"""
            Controls: tone={tone.value}; length={length.value}; cta={"yes" if include_cta else "no"}; hashtags={"yes" if include_hashtags else "no"}.
            """
        ).strip()
        self.last_draft_repair_performed = False
        draft = await self._ainvoke_text(
            [
                SystemMessage(content=DRAFT_FROM_ANSWER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Topic: {topic}\n\n"
                        f"Answer notes:\n{answer_notes}\n\n"
                        f"{option_block}\n\n"
                        "Create the final LinkedIn draft from these notes. Do not redo research."
                    )
                ),
            ],
            timeout_seconds=self._timeout_with_depth(settings.agent_plan_timeout_seconds),
        )
        if not self._looks_incomplete_draft(draft):
            return draft

        repaired = await self._ainvoke_text(
            [
                SystemMessage(content=DRAFT_COMPLETION_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Topic: {topic}\n\n"
                        f"Answer notes:\n{answer_notes}\n\n"
                        f"Unfinished draft:\n{draft}\n\n"
                        "Return a complete post. Keep it close to the original draft."
                    )
                ),
            ],
            timeout_seconds=self._timeout_with_depth(settings.agent_plan_timeout_seconds),
        )
        repaired = repaired.strip()
        if repaired and len(repaired) >= max(80, int(len(draft.strip()) * 0.8)):
            self.last_draft_repair_performed = True
            return repaired
        return draft

    @staticmethod
    def _looks_incomplete_draft(text: str) -> bool:
        cleaned = text.strip()
        if not cleaned:
            return True
        last_line = next((line.strip() for line in reversed(cleaned.splitlines()) if line.strip()), "")
        if not last_line:
            return True
        if last_line in {"-", "*", "•"} or re.match(r"^[-*•]\s*[\w&./+#-]{1,35}$", last_line):
            return True
        if last_line.endswith((",", ";", ":", "-", "and", "or", "with", "for", "to")):
            return True
        if not re.search(r'[.!?")\]#]$', last_line):
            return True
        return False

    @staticmethod
    def _compact_answer_for_draft(answer: str, *, length: DraftLength) -> str:
        limits = {
            DraftLength.short: 650,
            DraftLength.medium: 1250,
            DraftLength.long: 1700,
        }
        max_chars = limits.get(length, 850)
        cleaned_lines: list[str] = []
        for raw_line in answer.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = line.removeprefix("#").strip()
            if line.lower() in {"summary comparison", "why it matters", "practical example", "response"}:
                continue
            cleaned_lines.append(line)

        candidates = [AgentGraph._draft_note_candidate(line) for line in cleaned_lines]
        candidates = [candidate for candidate in candidates if candidate]
        priority_terms = (
            "generative",
            "builder",
            "pricing",
            "paid",
            "free",
            "trade-off",
            "tradeoff",
            "choose",
            "coding assistant",
            "top tools",
            "how they work",
        )
        priority_candidates = [
            candidate
            for candidate in candidates
            if any(term in candidate.lower() for term in priority_terms)
        ]
        ordered_candidates: list[str] = []
        for bucket in (candidates[:3], priority_candidates, candidates[3:]):
            for candidate in bucket:
                if candidate not in ordered_candidates:
                    ordered_candidates.append(candidate)

        selected: list[str] = []
        total = 0
        for candidate in ordered_candidates:
            if not candidate:
                continue
            normalized = " ".join(candidate.lower().split())
            if any(normalized == " ".join(item.lower().split()) for item in selected):
                continue
            added = len(candidate) + 1
            if selected and total + added > max_chars:
                break
            selected.append(candidate)
            total += added

        compact = "\n".join(selected).strip()
        return compact or answer[:max_chars].strip()

    @staticmethod
    def _draft_note_candidate(line: str) -> str:
        if line.startswith(("-", "*")) or line[:2].isdigit():
            return line[:220]
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if part.strip()]
        return (" ".join(sentences[:2]) if sentences else line)[:320]

    async def summarize_conversation(
        self,
        previous_summary: str,
        recent_messages: list[dict[str, str]],
    ) -> str:
        return await self._ainvoke_text(
            [
                SystemMessage(content=CONVERSATION_SUMMARY_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Previous summary:\n{previous_summary or 'No previous summary.'}\n\n"
                        f"Latest messages:\n{self._format_recent_messages(recent_messages)}"
                    )
                ),
            ],
            timeout_seconds=self._timeout_with_depth(settings.agent_conversation_summary_timeout_seconds),
        )

    async def stream_direct_draft(
        self,
        topic: str,
        *,
        conversation_summary: str = "",
        recent_messages: list[dict[str, str]] | None = None,
    ):
        context_block = self._conversation_context_block(conversation_summary, recent_messages or [])
        async for text in self._stream_text(
            [
                SystemMessage(content=DRAFT_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        context_block
                        + f"Topic: {topic}\n\n"
                        f"Depth guidance:\n{self._depth_response_guidance()}\n\n"
                        "Write the final LinkedIn-ready draft now."
                    )
                ),
            ],
            chunk_timeout_seconds=self._response_chunk_timeout(),
        ):
            yield text

    async def stream_rewrite(
        self,
        instruction: str,
        existing_draft: str,
        *,
        conversation_summary: str = "",
        recent_messages: list[dict[str, str]] | None = None,
    ):
        context_block = self._conversation_context_block(conversation_summary, recent_messages or [])
        async for text in self._stream_text(
            [
                SystemMessage(content=REWRITE_SYSTEM_PROMPT),
                HumanMessage(content=context_block + f"Rewrite instruction:\n{instruction}\n\nExisting draft:\n{existing_draft}"),
            ],
            chunk_timeout_seconds=self._response_chunk_timeout(),
        ):
            yield text

    async def stream_response(
        self,
        topic: str,
        plan: str,
        source_context: str,
        *,
        conversation_summary: str = "",
        recent_messages: list[dict[str, str]] | None = None,
        response_style: str = "",
    ):
        context_block = self._conversation_context_block(conversation_summary, recent_messages or [])
        async for text in self._stream_text(
            [
                SystemMessage(content=ANSWER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        context_block
                        + f"Topic: {topic}\n\n"
                        + (f"Working plan:\n{plan}\n\n" if plan.strip() else "")
                        + f"Research evidence:\n{source_context}\n\n"
                        + f"Response guidance:\n{self._depth_response_guidance()}\n\n"
                        + self._style_guidance(response_style)
                        + "Answer the user's request clearly and conversationally."
                    )
                ),
            ],
            chunk_timeout_seconds=self._response_chunk_timeout(),
        ):
            yield text
