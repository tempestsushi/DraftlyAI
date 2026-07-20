from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import anyio

from ..agents.content_selection import format_selected_context
from ..agents.graph import AgentGraph, resolve_research_profile
from ..agents.graph.llms import create_chat_model
from ..agents.retrieval import RagConfig, build_rag_source_context, format_rag_context
from ..agents.tools.web_fetch import fetch_source_content
from ..agents.tools.web_search import search_web, source_domain
from ..agents.content_selection.text import estimate_tokens
from ..config import settings
from ..models import ResearchDepth


@dataclass(slots=True)
class EvaluationAnswer:
    pipeline: str
    request_number: int
    answer: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    token_source: str
    elapsed_seconds: float


def run_rag_evaluation(
    prompt: str,
    research_depth: ResearchDepth,
    *,
    include_responses: bool = True,
) -> dict[str, object]:
    profile = resolve_research_profile(research_depth)
    started = perf_counter()

    search_started = perf_counter()
    candidates = search_web(
        prompt,
        max_results=profile.search_max_results,
        tavily_api_key=settings.tavily_api_key,
        tavily_search_depth=settings.tavily_search_depth,
    )
    search_seconds = perf_counter() - search_started

    fetch_started = perf_counter()
    fetched_sources = _fetch_sources(candidates, profile)
    fetch_seconds = perf_counter() - fetch_started

    extractive_started = perf_counter()
    extractive_context = AgentGraph.build_extractive_source_context(
        prompt,
        fetched_sources,
        source_context_token_budget=profile.source_context_token_budget,
        selected_idea_target=profile.source_context_idea_target,
    )
    extractive_context_text = format_selected_context(extractive_context)
    extractive_log = AgentGraph.format_content_selection_debug_log(
        extractive_context,
        source_count=len(fetched_sources),
    )
    extractive_seconds = perf_counter() - extractive_started

    rag_started = perf_counter()
    rag_config = RagConfig(
        top_k=profile.rag_top_k,
        chunk_size=profile.rag_chunk_size,
        chunk_overlap=profile.rag_chunk_overlap,
        source_char_limit=profile.rag_source_char_limit,
        provider=settings.rag_provider,
        embed_model=settings.rag_embed_model,
        ollama_base_url=settings.ollama_base_url,
        embedding_timeout_seconds=settings.rag_embedding_timeout_seconds,
    )
    rag_context = build_rag_source_context(prompt, fetched_sources, rag_config)
    rag_log = AgentGraph.format_rag_debug_log(rag_context, source_count=len(fetched_sources))
    rag_context_text = format_rag_context(rag_context, source_char_limit=rag_config.source_char_limit)
    rag_log_context_text = format_rag_context(
        rag_context,
        source_char_limit=rag_config.source_char_limit,
        include_scores=True,
        include_urls=True,
    )
    rag_seconds = perf_counter() - rag_started

    answers: list[EvaluationAnswer] = []
    if include_responses:
        answers = anyio.run(
            _generate_evaluation_answers,
            prompt,
            research_depth,
            extractive_context_text,
            rag_context_text,
        )

    log_text = _format_evaluation_log(
        prompt=prompt,
        depth=research_depth,
        candidates=candidates,
        fetched_sources=fetched_sources,
        search_seconds=search_seconds,
        fetch_seconds=fetch_seconds,
        extractive_seconds=extractive_seconds,
        rag_seconds=rag_seconds,
        extractive_log=extractive_log,
        rag_log=rag_log,
        rag_context_text=rag_log_context_text,
        answers=answers,
    )
    log_path = _append_evaluation_log(log_text)

    return {
        "ok": True,
        "log_path": str(log_path),
        "candidate_sources": len(candidates),
        "fetched_sources": len(fetched_sources),
        "extractive_selected": len(extractive_context.selected_items),
        "rag_selected": len(rag_context.selected_chunks),
        "rag_retrieval_mode": rag_context.debug_metrics.get("rag_retrieval_mode", "lexical_fallback"),
        "llm_requests": len(answers),
        "elapsed_seconds": round(perf_counter() - started, 2),
    }


async def _generate_evaluation_answers(
    prompt: str,
    research_depth: ResearchDepth,
    extractive_context_text: str,
    rag_context_text: str,
) -> list[EvaluationAnswer]:
    return [
        await _generate_evaluation_answer(
            request_number=1,
            pipeline="extractive",
            prompt=prompt,
            research_depth=research_depth,
            source_context=extractive_context_text,
        ),
        await _generate_evaluation_answer(
            request_number=2,
            pipeline="rag",
            prompt=prompt,
            research_depth=research_depth,
            source_context=rag_context_text,
        ),
    ]


async def _generate_evaluation_answer(
    *,
    request_number: int,
    pipeline: str,
    prompt: str,
    research_depth: ResearchDepth,
    source_context: str,
) -> EvaluationAnswer:
    profile = resolve_research_profile(research_depth)
    agent = AgentGraph(
        llm=create_chat_model(max_output_tokens=profile.gemini_output_tokens),
        graph=None,
        research_profile=profile,
    )
    started = perf_counter()
    answer = await agent.build_grounded_response(
        prompt,
        "Use the provided research evidence only.",
        source_context,
    )
    elapsed = perf_counter() - started
    usage = agent.consume_usage_metadata()
    input_tokens, output_tokens, total_tokens, token_source = _token_metrics_from_usage(
        usage,
        prompt=prompt,
        source_context=source_context,
        answer=answer,
    )
    return EvaluationAnswer(
        pipeline=pipeline,
        request_number=request_number,
        answer=answer,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        token_source=token_source,
        elapsed_seconds=elapsed,
    )


def _fetch_sources(candidates: list[dict[str, str]], profile) -> list[dict[str, str]]:
    fetched_sources: list[dict[str, str]] = []
    for source in candidates[: profile.fetch_max_sources]:
        try:
            fetched = fetch_source_content(
                source["url"],
                user_agent=settings.web_user_agent,
                char_limit=profile.extract_char_limit,
                timeout_seconds=settings.agent_fetch_timeout_seconds,
            )
            content = fetched.get("content", "")
            fetch_status = "page extract"
        except Exception as exc:
            content = source.get("snippet", "")
            fetch_status = f"snippet fallback: {str(exc)[:120]}"
        fetched_sources.append(
            {
                **source,
                "domain": source_domain(source.get("url", "")),
                "content": content,
                "fetch_status": fetch_status,
            }
        )
    return fetched_sources


def _append_evaluation_log(log_text: str) -> Path:
    path = Path(settings.rag_evaluation_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(log_text)
        file.write("\n\n")
    return path


def _format_evaluation_log(
    *,
    prompt: str,
    depth: ResearchDepth,
    candidates: list[dict[str, str]],
    fetched_sources: list[dict[str, str]],
    search_seconds: float,
    fetch_seconds: float,
    extractive_seconds: float,
    rag_seconds: float,
    extractive_log: str,
    rag_log: str,
    rag_context_text: str,
    answers: list[EvaluationAnswer],
) -> str:
    lines = [
        "=" * 88,
        f"RAG Evaluation | {datetime.now(timezone.utc).isoformat()}",
        f"Prompt: {prompt}",
        f"Depth: {depth.value}",
        "",
        "Shared Search/Fetch",
        f"- candidate sources: {len(candidates)}",
        f"- fetched sources: {len(fetched_sources)}",
        f"- search time: {search_seconds:.2f}s",
        f"- fetch/extract time: {fetch_seconds:.2f}s",
        "",
        "Candidate Sources",
        *_format_sources(candidates),
        "",
        "Fetched Sources",
        *_format_fetched_sources(fetched_sources),
        "",
        f"Extractive Pipeline ({extractive_seconds:.2f}s)",
        extractive_log,
        "",
        f"RAG Pipeline ({rag_seconds:.2f}s)",
        rag_log,
        "",
        "RAG Selected Chunks",
        rag_context_text,
        "",
        "Generated Responses",
        *_format_answers(answers),
    ]
    return "\n".join(lines)


def _format_sources(sources: list[dict[str, str]]) -> list[str]:
    if not sources:
        return ["- none"]
    return [
        f"{index}. {source.get('title', 'Untitled')} | {source_domain(source.get('url', ''))}\n"
        f"   URL: {source.get('url', '')}\n"
        f"   Snippet: {' '.join(source.get('snippet', '').split())[:260]}"
        for index, source in enumerate(sources, start=1)
    ]


def _format_fetched_sources(sources: list[dict[str, str]]) -> list[str]:
    if not sources:
        return ["- none"]
    return [
        f"{index}. {source.get('title', 'Untitled')} | {source.get('domain', '')} | "
        f"{source.get('fetch_status', 'unknown')} | {len(source.get('content', ''))} chars"
        for index, source in enumerate(sources, start=1)
    ]


def _format_answers(answers: list[EvaluationAnswer]) -> list[str]:
    if not answers:
        return ["- skipped. Send include_responses=true to generate answers."]
    lines: list[str] = []
    for answer in answers:
        lines.extend(
            [
                f"LLM request #{answer.request_number} | {answer.pipeline}",
                f"- input tokens: {answer.input_tokens} ({answer.token_source})",
                f"- output tokens: {answer.output_tokens} ({answer.token_source})",
                f"- total tokens: {answer.total_tokens} ({answer.token_source})",
                f"- generation time: {answer.elapsed_seconds:.2f}s",
                "Response:",
                answer.answer.strip() or "[empty response]",
                "",
            ]
        )
    return lines


def _token_metrics_from_usage(
    usage: dict | None,
    *,
    prompt: str,
    source_context: str,
    answer: str,
) -> tuple[int, int, int, str]:
    if usage:
        input_tokens = usage.get("input_tokens") or usage.get("prompt_token_count") or usage.get("prompt_tokens")
        output_tokens = (
            usage.get("output_tokens")
            or usage.get("completion_token_count")
            or usage.get("completion_tokens")
        )
        total_tokens = usage.get("total_tokens") or usage.get("total_token_count")
        if input_tokens is not None and output_tokens is not None:
            total = int(total_tokens) if total_tokens is not None else int(input_tokens) + int(output_tokens)
            return int(input_tokens), int(output_tokens), total, "provider"

    estimated_input = estimate_tokens(
        " ".join(
            [
                prompt,
                "Use the provided research evidence only.",
                source_context,
            ]
        )
    )
    estimated_output = estimate_tokens(answer)
    return estimated_input, estimated_output, estimated_input + estimated_output, "estimated"
