from __future__ import annotations

import asyncio
import logging
import sys
import time
from collections.abc import AsyncIterator
from urllib.parse import urlparse

from ...agents import AgentIntent
from ...agents.streaming import chunk_text, sse_event
from ...config import settings
from ...models import DraftRecord, LogSource, MessageRole, ResearchDepth, TopicStatus
from ...store import Store
from .fallbacks import build_response_timeout_fallback
from .memory import should_update_conversation_summary
from .prompt_context import resolve_regeneration_prompt, sanitize_response_style
from .sources import normalize_sources
from .telemetry import format_usage_log, friendly_agent_error, stream_text_event

logger = logging.getLogger(__name__)


def _agent_api():
    return sys.modules[__package__]


def _source_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.removeprefix("www.") if parsed.netloc else "unknown"


def _compact_text(value: str, limit: int = 120) -> str:
    compacted = " ".join(value.split())
    if len(compacted) <= limit:
        return compacted
    return f"{compacted[:limit].rstrip()}..."


def _format_search_sources(search_results: list[dict], *, limit: int = 5) -> str:
    if not search_results:
        return "Candidate sources:\nNo search results were returned."
    lines = ["Candidate sources:"]
    for index, result in enumerate(search_results[:limit], start=1):
        title = _compact_text(str(result.get("title") or "Untitled source"), 80)
        url = str(result.get("url") or "").strip()
        snippet = _compact_text(str(result.get("snippet") or "No snippet"), 120)
        lines.append(f"{index}. {title} | {_source_domain(url)}")
        if url:
            lines.append(f"   URL: {url}")
        lines.append(f"   Snippet: {snippet}")
    return "\n".join(lines)


def _format_fetched_sources(fetched_sources: list[dict], *, limit: int = 5) -> str:
    if not fetched_sources:
        return "Fetched source detail:\nNo source pages were extracted."
    lines = ["Fetched source detail:"]
    for index, source in enumerate(fetched_sources[:limit], start=1):
        title = _compact_text(str(source.get("title") or "Untitled source"), 80)
        url = str(source.get("url") or "").strip()
        content = " ".join(str(source.get("content") or "").split())
        snippet = " ".join(str(source.get("snippet") or "").split())
        mode = "page extract" if content else "snippet fallback"
        char_count = len(content or snippet)
        lines.append(f"{index}. {title} | {_source_domain(url)} | {mode} | {char_count} chars")
        if url:
            lines.append(f"   URL: {url}")
    return "\n".join(lines)


def _prior_sources_for_topic(store: Store, topic_id: str, *, limit: int = 4) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for source in reversed(store.list_message_sources(topic_id)):
        url = source.url.strip()
        if not url or url in seen_urls:
            continue
        sources.append(
            {
                "title": source.title,
                "url": url,
                "snippet": source.snippet or "",
                "domain": source.domain or "",
            }
        )
        seen_urls.add(url)
        if len(sources) >= limit:
            break
    return list(reversed(sources))


async def _graph_updates_with_heartbeat(graph: object, state: dict, *, heartbeat_seconds: float = 4.0):
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    async def pump_updates() -> None:
        try:
            async for update in graph.astream(state, stream_mode="updates"):
                await queue.put(("update", update))
        except Exception as exc:
            await queue.put(("error", exc))
        finally:
            await queue.put(("done", None))

    task = asyncio.create_task(pump_updates())
    try:
        while True:
            try:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
            except asyncio.TimeoutError:
                yield "heartbeat", None
                continue

            if kind == "update":
                yield kind, payload
            elif kind == "error":
                raise payload
            else:
                break
    finally:
        if not task.done():
            task.cancel()


async def _async_iter_with_heartbeat(source, *, heartbeat_seconds: float = 4.0):
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    async def pump_items() -> None:
        try:
            async for item in source:
                await queue.put(("item", item))
        except Exception as exc:
            await queue.put(("error", exc))
        finally:
            await queue.put(("done", None))

    task = asyncio.create_task(pump_items())
    try:
        while True:
            try:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
            except asyncio.TimeoutError:
                yield "heartbeat", None
                continue

            if kind == "item":
                yield kind, payload
            elif kind == "error":
                raise payload
            else:
                break
    finally:
        if not task.done():
            task.cancel()


async def stream_agent_run(
    store: Store,
    topic: str,
    *,
    topic_id: str | None = None,
    research_depth: ResearchDepth = ResearchDepth.moderate,
    regenerate_message_id: str | None = None,
    replace_user_message_id: str | None = None,
    response_style: str | None = None,
) -> AsyncIterator[str]:
    topic, is_regeneration = resolve_regeneration_prompt(store, topic_id, regenerate_message_id, topic)
    response_style = sanitize_response_style(response_style)
    decision = _agent_api().classify_request(topic)
    if decision.intent == AgentIntent.linkedin_draft:
        agent = _agent_api().create_agent_graph(
            research_depth=research_depth,
            max_output_tokens=settings.gemini_draft_output_tokens,
        )
    else:
        agent = _agent_api().create_agent_graph(research_depth=research_depth)
    research_profile = getattr(agent, "research_profile", None)
    existing_topic = store.get_topic(topic_id) if topic_id else None
    if existing_topic is not None:
        record = store.update_topic_status(existing_topic.id, TopicStatus.searching) or existing_topic
    else:
        record = store.create_topic(topic, TopicStatus.searching)
    if replace_user_message_id:
        existing_message = next(
            (message for message in store.list_messages(record.id) if message.id == replace_user_message_id),
            None,
        )
        if existing_message is None:
            raise ValueError("The original prompt was not found in this chat")
        if existing_message.role != MessageRole.user:
            raise ValueError("Only user prompts can be edited")
        user_message = store.update_message(record.id, replace_user_message_id, topic)
        if user_message is None:
            raise ValueError("The original prompt could not be updated")
        yield sse_event("user_message", user_message.model_dump(mode="json"))
    elif not is_regeneration:
        user_message = store.add_message(record.id, MessageRole.user, topic)
        yield sse_event("user_message", user_message.model_dump(mode="json"))
    else:
        regen_log = store.add_log(record.id, LogSource.system, "Regenerating answer from the selected chat prompt")
        yield sse_event("log", regen_log.model_dump(mode="json"))
    recent_limit = min(settings.chat_recent_messages_limit, 5)
    recent_messages = [
        {"role": message.role.value, "content": message.content}
        for message in store.list_recent_messages(record.id, limit=recent_limit)
    ]
    conversation_summary = record.conversation_summary or ""
    prior_sources = _prior_sources_for_topic(store, record.id) if existing_topic is not None else []
    yield sse_event("status", {"topicId": record.id, "state": TopicStatus.searching})

    search_log = store.add_log(record.id, LogSource.system, "Initializing agent runtime")
    yield sse_event("log", search_log.model_dump(mode="json"))
    route_log = store.add_log(
        record.id,
        LogSource.system,
        f"Workflow selected: {decision.intent.value} ({decision.reason}); depth={research_depth.value}",
    )
    yield sse_event("log", route_log.model_dump(mode="json"))
    if research_profile is not None:
        depth_log = store.add_log(
            record.id,
            LogSource.system,
            (
                f"Depth profile {research_depth.value}: "
                f"{research_profile.fetch_max_sources} source(s), "
                f"{research_profile.min_thinking_seconds}-{research_profile.max_thinking_seconds}s thinking window"
            ),
        )
        yield sse_event("log", depth_log.model_dump(mode="json"))
    await asyncio.sleep(0.35)

    try:
        run_started_at = time.monotonic()
        plan = ""
        source_context = ""
        response_sources: list[dict[str, str | None]] = []

        response_parts: list[str] = []
        if decision.intent == AgentIntent.research:
            store.update_topic_status(record.id, TopicStatus.drafting)
            yield sse_event("status", {"topicId": record.id, "state": TopicStatus.drafting})

            research_state: dict = {
                "topic_id": record.id,
                "topic": topic,
                "research_depth": research_depth,
                "conversation_summary": conversation_summary,
                "recent_messages": recent_messages,
                "prior_sources": prior_sources,
            }
            async for update_kind, update in _graph_updates_with_heartbeat(agent.graph, research_state):
                if update_kind == "heartbeat":
                    yield sse_event("heartbeat", {"topicId": record.id, "state": "working"})
                    continue
                for node_name, node_payload in update.items():
                    research_state.update(node_payload)

                    if node_name in {"prepare_query", "generate_plan"}:
                        query = str(node_payload.get("search_query") or topic).strip()
                        query_log = store.add_log(record.id, LogSource.system, f"Search query prepared: {query}")
                        yield sse_event(
                            "tool_result",
                            {"topicId": record.id, "source": LogSource.system, "message": "Search query prepared"},
                        )
                        yield sse_event("log", query_log.model_dump(mode="json"))
                        planner_warning = str(node_payload.get("planner_warning", "")).strip()
                        if planner_warning:
                            warning_log = store.add_log(record.id, LogSource.system, planner_warning)
                            yield sse_event("log", warning_log.model_dump(mode="json"))
                        search_start = store.add_log(record.id, LogSource.web_search, f"Searching the web for: {topic}")
                        yield sse_event("tool_start", search_start.model_dump(mode="json"))
                    elif node_name == "search_web":
                        count = len(node_payload.get("search_results", []))
                        queries_used = node_payload.get("search_queries") or [node_payload.get("search_query", topic)]
                        query_label = "; ".join(str(query).strip() for query in queries_used if str(query).strip())
                        search_done = store.add_log(record.id, LogSource.web_search, f"Found {count} candidate sources")
                        yield sse_event(
                            "tool_result",
                            {
                                "topicId": record.id,
                                "source": LogSource.web_search,
                                "message": f"Found {count} sources using: {query_label}",
                            },
                        )
                        yield sse_event("log", search_done.model_dump(mode="json"))
                        search_detail = store.add_log(
                            record.id,
                            LogSource.web_search,
                            _format_search_sources(node_payload.get("search_results", [])),
                        )
                        yield sse_event("log", search_detail.model_dump(mode="json"))
                        fetch_start = store.add_log(record.id, LogSource.web_fetch, "Fetching and extracting source pages")
                        yield sse_event("tool_start", fetch_start.model_dump(mode="json"))
                    elif node_name == "fetch_sources":
                        count = len(node_payload.get("fetched_sources", []))
                        fetch_done = store.add_log(record.id, LogSource.web_fetch, f"Extracted {count} source pages")
                        yield sse_event(
                            "tool_result",
                            {"topicId": record.id, "source": LogSource.web_fetch, "message": f"Extracted {count} pages"},
                        )
                        yield sse_event("log", fetch_done.model_dump(mode="json"))
                        fetch_detail = store.add_log(
                            record.id,
                            LogSource.web_fetch,
                            _format_fetched_sources(node_payload.get("fetched_sources", [])),
                        )
                        yield sse_event("log", fetch_detail.model_dump(mode="json"))
                        summarize_start = store.add_log(record.id, LogSource.system, "Building local evidence notes")
                        yield sse_event("tool_start", summarize_start.model_dump(mode="json"))
                    elif node_name == "summarize_sources":
                        evidence_mode = str(node_payload.get("evidence_mode") or "extractive")
                        if evidence_mode == "extractive_fallback":
                            reason = str(node_payload.get("evidence_error") or "source context was unavailable").strip()
                            evidence_message = f"Source context selection fell back to extractive evidence ({reason})"
                        elif evidence_mode == "rag":
                            evidence_message = "RAG retrieval context prepared"
                        else:
                            evidence_message = "Extractive source evidence prepared"
                        summary_done = store.add_log(record.id, LogSource.system, evidence_message)
                        yield sse_event(
                            "tool_result",
                            {"topicId": record.id, "source": LogSource.system, "message": evidence_message},
                        )
                        yield sse_event("log", summary_done.model_dump(mode="json"))
                        selection_debug_log = str(node_payload.get("content_selection_debug_log") or "").strip()
                        if selection_debug_log:
                            debug_log = store.add_log(record.id, LogSource.system, selection_debug_log)
                            yield sse_event("log", debug_log.model_dump(mode="json"))

            plan = research_state.get("plan", "")
            source_context = research_state.get("source_context", "")
            response_sources = normalize_sources(
                research_state.get("fetched_sources", []),
                research_state.get("search_results", []),
            )
            if not response_sources:
                no_sources_log = store.add_log(
                    record.id,
                    LogSource.system,
                    "No strong source context was selected; answering with limited grounding.",
                )
                yield sse_event("log", no_sources_log.model_dump(mode="json"))
            if research_profile is not None:
                elapsed = time.monotonic() - run_started_at
                wait_seconds = max(0.0, research_profile.min_thinking_seconds - elapsed)
                if wait_seconds > 0:
                    pacing_log = store.add_log(
                        record.id,
                        LogSource.system,
                        f"Holding response briefly to match {research_depth.value} depth pacing ({wait_seconds:.1f}s)",
                    )
                    yield sse_event("log", pacing_log.model_dump(mode="json"))
                    await asyncio.sleep(wait_seconds)
            draft_start = store.add_log(record.id, LogSource.ollama, "Generating source-grounded answer")
            yield sse_event("tool_start", draft_start.model_dump(mode="json"))
            try:
                answer_stream = agent.stream_response(
                    topic,
                    plan,
                    source_context,
                    conversation_summary=conversation_summary,
                    recent_messages=recent_messages,
                    response_style=response_style,
                )
                async for item_kind, chunk in _async_iter_with_heartbeat(answer_stream):
                    if item_kind == "heartbeat":
                        yield sse_event("heartbeat", {"topicId": record.id, "state": "generating_answer"})
                        continue
                    response_parts.append(chunk)
                    for event in stream_text_event("answer_chunk", record.id, chunk):
                        yield event
            except asyncio.TimeoutError:
                timeout_log = store.add_log(
                    record.id,
                    LogSource.system,
                    "Final answer stream timed out; saving selected research context instead.",
                )
                yield sse_event("log", timeout_log.model_dump(mode="json"))
                if not response_parts:
                    fallback_text = build_response_timeout_fallback(source_context)
                    response_parts.append(fallback_text)
                    for event in stream_text_event("answer_chunk", record.id, fallback_text):
                        yield event
        elif decision.intent == AgentIntent.rewrite:
            store.update_topic_status(record.id, TopicStatus.drafting)
            yield sse_event("status", {"topicId": record.id, "state": TopicStatus.drafting})
            drafts = [draft for draft in store.list_drafts() if draft.topic_id == record.id]
            existing_draft = drafts[0].content if drafts else ""
            rewrite_start = store.add_log(record.id, LogSource.ollama, "Rewriting the latest draft")
            yield sse_event("tool_start", rewrite_start.model_dump(mode="json"))
            if not existing_draft:
                raise ValueError("I could not find an existing draft in this thread to rewrite. Generate one first.")
            else:
                rewrite_stream = agent.stream_rewrite(
                    topic,
                    existing_draft,
                    conversation_summary=conversation_summary,
                    recent_messages=recent_messages,
                )
                async for item_kind, chunk in _async_iter_with_heartbeat(rewrite_stream):
                    if item_kind == "heartbeat":
                        yield sse_event("heartbeat", {"topicId": record.id, "state": "rewriting"})
                        continue
                    response_parts.append(chunk)
                    for piece in chunk_text(chunk, 28):
                        yield sse_event("draft_chunk", {"topicId": record.id, "text": piece})
        else:
            store.update_topic_status(record.id, TopicStatus.drafting)
            yield sse_event("status", {"topicId": record.id, "state": TopicStatus.drafting})
            draft_start = store.add_log(record.id, LogSource.ollama, "Generating direct LinkedIn draft with Ollama")
            yield sse_event("tool_start", draft_start.model_dump(mode="json"))
            direct_draft_stream = agent.stream_direct_draft(
                topic,
                conversation_summary=conversation_summary,
                recent_messages=recent_messages,
            )
            async for item_kind, chunk in _async_iter_with_heartbeat(direct_draft_stream):
                if item_kind == "heartbeat":
                    yield sse_event("heartbeat", {"topicId": record.id, "state": "drafting"})
                    continue
                response_parts.append(chunk)
                for piece in chunk_text(chunk, 28):
                    yield sse_event("draft_chunk", {"topicId": record.id, "text": piece})

        response_text = "".join(response_parts).strip()
        usage = agent.consume_usage_metadata() if hasattr(agent, "consume_usage_metadata") else None
        usage_log = store.add_log(
            record.id,
            LogSource.system,
            format_usage_log(usage, response_text=response_text, elapsed_seconds=time.monotonic() - run_started_at),
        )
        yield sse_event("log", usage_log.model_dump(mode="json"))
        assistant_message = store.add_message(record.id, MessageRole.assistant, response_text)
        if response_sources:
            store.add_message_sources(record.id, assistant_message.id, response_sources)
        updated_recent_messages = [
            {"role": message.role.value, "content": message.content}
            for message in store.list_recent_messages(record.id, limit=recent_limit)
        ]
        user_message_count = sum(1 for message in store.list_messages(record.id) if message.role == MessageRole.user)
        should_update_memory = should_update_conversation_summary(
            research_depth,
            decision.intent,
            user_message_count,
        )
        if should_update_memory:
            try:
                updated_summary = await agent.summarize_conversation(conversation_summary, updated_recent_messages)
            except asyncio.TimeoutError:
                updated_summary = conversation_summary
                memory_log = store.add_log(
                    record.id,
                    LogSource.system,
                    "Conversation summary timed out; keeping the previous chat memory.",
                )
                yield sse_event("log", memory_log.model_dump(mode="json"))
        else:
            updated_summary = conversation_summary
            memory_log = store.add_log(
                record.id,
                LogSource.system,
                "Quick mode skipped conversation summary update to save model requests.",
            )
            yield sse_event("log", memory_log.model_dump(mode="json"))
        updated_summary = updated_summary.strip()
        if len(updated_summary) > settings.chat_summary_char_limit:
            updated_summary = f"{updated_summary[:settings.chat_summary_char_limit].rstrip()}..."
        draft: DraftRecord | None = None
        if decision.intent == AgentIntent.research:
            store.update_topic_response(
                record.id,
                response_content=response_text,
                conversation_summary=updated_summary,
                status=TopicStatus.complete,
            )
            completion_log = store.add_log(record.id, LogSource.system, "Answer generated and saved to this chat")
            final_state = TopicStatus.complete
            final_message = "Answer generation complete"
        else:
            draft = store.add_draft(
                title=topic,
                content=response_text,
                source="research",
                topic_id=record.id,
                source_message_id=assistant_message.id,
            )
            store.update_topic_response(
                record.id,
                response_content=response_text,
                conversation_summary=updated_summary,
                status=TopicStatus.review,
            )
            completion_log = store.add_log(record.id, LogSource.system, "Draft created and queued for approval")
            final_state = TopicStatus.review
            final_message = "Draft generation complete"
        yield sse_event(
            "tool_result",
            {"topicId": record.id, "source": LogSource.ollama, "message": final_message},
        )
        yield sse_event("log", completion_log.model_dump(mode="json"))
        yield sse_event(
            "done",
            {
                "topicId": record.id,
                "state": final_state,
                "assistantMessageId": assistant_message.id,
                "response": response_text,
                "draft": draft.model_dump(mode="json") if draft else None,
                "sources": response_sources,
                "error": None,
            },
        )
    except asyncio.CancelledError:
        store.update_topic_status(record.id, TopicStatus.error)
        cancel_log = store.add_log(record.id, LogSource.system, "Generation canceled by the client")
        yield sse_event("log", cancel_log.model_dump(mode="json"))
        raise
    except Exception as exc:
        friendly_error = friendly_agent_error(exc)
        store.update_topic_status(record.id, TopicStatus.error)
        logger.exception("Agent run failed for topic_id=%s", record.id)
        error_log = store.add_log(record.id, LogSource.system, f"Agent run failed: {friendly_error}")
        yield sse_event("log", error_log.model_dump(mode="json"))
        yield sse_event(
            "done",
            {
                "topicId": record.id,
                "state": TopicStatus.error,
                "response": "",
                "draft": None,
                "sources": [],
                "error": friendly_error,
            },
        )
