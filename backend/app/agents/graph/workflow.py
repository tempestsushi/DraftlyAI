from __future__ import annotations

import asyncio
import math
import re
from urllib.parse import urlparse

from langgraph.graph import END, StateGraph

from ...config import settings
from ...models import ResearchDepth
from ..search_queries import build_search_query
from ..state import AgentState
from ..tools import fetch_source_content, search_web
from ..tools.web_search import canonical_source_url, is_text_source_url, source_domain
from .helper import AgentGraph
from .llms import create_chat_model
from .profiles import resolve_research_profile


def create_agent_graph(
    research_depth: ResearchDepth = ResearchDepth.moderate,
    *,
    max_output_tokens: int | None = None,
) -> AgentGraph:
    research_profile = resolve_research_profile(research_depth)
    llm = create_chat_model(max_output_tokens=max_output_tokens or research_profile.gemini_output_tokens)

    workflow = StateGraph(AgentState)
    helper = AgentGraph(llm=llm, graph=None, research_profile=research_profile)

    def extract_prompt_urls(topic: str) -> list[str]:
        urls: list[str] = []
        for raw_url in re.findall(r"https?://[^\s<>)\]}\"']+", topic):
            url = canonical_source_url(raw_url.rstrip(".,;:!?"))
            if url and is_text_source_url(url) and url not in urls:
                urls.append(url)
        return urls

    def title_from_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc.endswith("github.com") and parsed.path.strip("/"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                return f"GitHub repository: {parts[0]}/{parts[1]}"
        title = parsed.path.strip("/").replace("-", " ").replace("_", " ").strip()
        return title[:80] or source_domain(url) or url

    def fetch_urls_for_source(url: str) -> list[str]:
        parsed = urlparse(url)
        candidates = [url]
        if parsed.netloc.lower().endswith("github.com"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 2:
                owner, repo = parts
                candidates = [
                    f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
                    f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
                    url,
                ]
        canonical_url = canonical_source_url(url)
        if canonical_url and canonical_url not in candidates:
            candidates.append(canonical_url)
        if parsed.path and not url.endswith("/"):
            slash_url = f"{url}/"
            if slash_url not in candidates:
                candidates.append(slash_url)
        if parsed.query:
            without_query = parsed._replace(query="", fragment="").geturl()
            if without_query and without_query not in candidates:
                candidates.append(without_query)
        if parsed.fragment:
            without_fragment = parsed._replace(fragment="").geturl()
            if without_fragment and without_fragment not in candidates:
                candidates.append(without_fragment)
        if parsed.path.strip("/") and parsed.netloc:
            base_url = parsed._replace(path="", params="", query="", fragment="").geturl()
            if base_url and base_url not in candidates:
                candidates.append(base_url)
        return candidates[:5]

    async def prepare_query_node(state: AgentState) -> AgentState:
        recent_messages = state.get("recent_messages", [])
        recent_limit = min(settings.chat_recent_messages_limit, 5)
        conversation_summary = state.get("conversation_summary", "")[: settings.chat_summary_char_limit]
        search_query = build_search_query(
            state["topic"],
            conversation_summary=conversation_summary,
            recent_messages=recent_messages[-recent_limit:],
        )

        search_queries = helper.build_search_query_variants(
            state["topic"],
            search_query,
            research_profile.search_query_count,
        )
        return {
            "plan": "",
            "search_query": search_queries[0] if search_queries else search_query,
            "search_queries": search_queries,
        }

    async def search_node(state: AgentState) -> AgentState:
        queries = state.get("search_queries") or [(state.get("search_query") or state["topic"]).strip()]
        prompt_urls = extract_prompt_urls(state["topic"])
        prior_source_urls = [
            canonical_source_url(str(source.get("url", "")).strip())
            for source in state.get("prior_sources", [])
            if source.get("url")
        ]
        reusable_urls = prompt_urls or [
            url for url in prior_source_urls if url and is_text_source_url(url)
        ]
        user_sources = [
            {
                "title": title_from_url(url),
                "url": url,
                "snippet": "User-provided source URL." if prompt_urls else "Previously used source URL from this chat.",
                "source_priority": "user_provided" if prompt_urls else "chat_context",
            }
            for url in reusable_urls
        ]
        if user_sources:
            return {
                "search_results": user_sources[: research_profile.search_max_results],
                "search_query": queries[0],
                "search_queries": queries,
                "user_source_urls": reusable_urls,
            }
        per_query_limit = max(1, math.ceil(research_profile.search_max_results / len(queries)))

        async def run_query(query: str) -> list[dict[str, str]]:
            return await asyncio.to_thread(
                search_web,
                query,
                max_results=max(1, per_query_limit),
                tavily_api_key=settings.tavily_api_key,
                tavily_search_depth=settings.tavily_search_depth,
            )

        query_results = await asyncio.wait_for(
            asyncio.gather(*(run_query(query) for query in queries)),
            timeout=settings.agent_search_timeout_seconds,
        )
        raw_results = [result for results in query_results for result in results]
        results = helper.rank_search_results(state["topic"], raw_results)
        return {
            "search_results": results[: research_profile.search_max_results],
            "search_query": queries[0],
            "search_queries": queries,
        }

    async def fetch_node(state: AgentState) -> AgentState:
        search_results = state.get("search_results", [])
        selected_results = search_results[: research_profile.fetch_max_sources]
        semaphore = asyncio.Semaphore(4)

        def snippet_source(result: dict[str, str]) -> dict[str, str]:
            return {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "content": "",
            }

        def is_usable_snippet(result: dict[str, str]) -> bool:
            return helper.is_source_content_usable(snippet_source(result))

        def backfill_with_snippets(
            fetched_sources: list[dict[str, str]],
            candidates: list[dict[str, str]],
        ) -> list[dict[str, str]]:
            sources = list(fetched_sources[: research_profile.fetch_max_sources])
            if len(sources) >= research_profile.fetch_max_sources:
                return sources
            seen_urls = {source.get("url", "") for source in sources}
            for result in candidates:
                url = result.get("url", "")
                if url in seen_urls or not is_usable_snippet(result):
                    continue
                sources.append(snippet_source(result))
                seen_urls.add(url)
                if len(sources) >= research_profile.fetch_max_sources:
                    break
            return sources

        async def fetch_one(result: dict[str, str]) -> dict[str, str] | None:
            last_error = ""
            for fetch_url in fetch_urls_for_source(result["url"]):
                for attempt in range(2):
                    try:
                        async with semaphore:
                            fetched = await asyncio.wait_for(
                                asyncio.to_thread(
                                    fetch_source_content,
                                    fetch_url,
                                    user_agent=settings.web_user_agent,
                                    char_limit=research_profile.extract_char_limit,
                                    timeout_seconds=settings.agent_fetch_timeout_seconds,
                                ),
                                timeout=settings.agent_fetch_timeout_seconds + 1,
                            )
                        source = {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": result.get("snippet", ""),
                            "content": fetched.get("content", ""),
                            "fetch_url": fetch_url,
                        }
                        if not helper.is_source_content_usable(source):
                            return None
                        return source
                    except Exception as exc:
                        last_error = str(exc)
                        if attempt == 0 and _is_transient_fetch_error(exc):
                            await asyncio.sleep(0.25)
                            continue
                        break
            fallback = snippet_source(result)
            fallback["fetch_error"] = _friendly_fetch_error(last_error)
            return fallback if is_usable_snippet(fallback) else None

        def is_strong_fetch(source: dict[str, str]) -> bool:
            content = " ".join((source.get("content") or "").split())
            return len(content) >= 250 and len(content.split()) >= 40

        async def fetch_until_filled() -> list[dict[str, str]]:
            fetched_sources: list[dict[str, str]] = []
            weak_snippet_sources: list[dict[str, str]] = []
            seen_urls: set[str] = set()
            cursor = 0
            batch_size = max(1, research_profile.fetch_max_sources)

            while len(fetched_sources) < research_profile.fetch_max_sources and cursor < len(search_results):
                batch: list[dict[str, str]] = []
                while len(batch) < batch_size and cursor < len(search_results):
                    result = search_results[cursor]
                    cursor += 1
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        batch.append(result)
                        seen_urls.add(url)
                if not batch:
                    break

                fetched_results = await asyncio.gather(
                    *(fetch_one(result) for result in batch),
                    return_exceptions=False,
                )
                for source in fetched_results:
                    if source is None:
                        continue
                    if is_strong_fetch(source):
                        fetched_sources.append(source)
                    elif is_usable_snippet(source):
                        weak_snippet_sources.append(snippet_source(source))
                    if len(fetched_sources) >= research_profile.fetch_max_sources:
                        break

            return backfill_with_snippets(fetched_sources + weak_snippet_sources, search_results)

        if not research_profile.fetch_enabled:
            snippet_sources = [
                snippet_source(result)
                for result in selected_results
                if is_usable_snippet(result)
            ]
            if snippet_sources:
                return {"fetched_sources": snippet_sources}

            weak_fetches = await asyncio.gather(
                *(fetch_one(result) for result in selected_results),
                return_exceptions=False,
            )
            return {
                "fetched_sources": backfill_with_snippets(
                    [source for source in weak_fetches if source is not None],
                    selected_results,
                )
            }

        return {"fetched_sources": await fetch_until_filled()}

    async def summarize_node(state: AgentState) -> AgentState:
        summary = await helper.summarize_sources(
            state["topic"],
            state.get("fetched_sources", []),
        )
        return {
            "source_context": summary,
            "evidence_mode": "rag" if settings.rag_enabled else "extractive",
            "content_selection_debug_log": helper.consume_content_selection_debug_log(),
        }

    workflow.add_node("prepare_query", prepare_query_node)
    workflow.add_node("search_web", search_node)
    workflow.add_node("fetch_sources", fetch_node)
    workflow.add_node("summarize_sources", summarize_node)
    workflow.set_entry_point("prepare_query")
    workflow.add_edge("prepare_query", "search_web")
    workflow.add_edge("search_web", "fetch_sources")
    workflow.add_edge("fetch_sources", "summarize_sources")
    workflow.add_edge("summarize_sources", END)

    return AgentGraph(llm=llm, graph=workflow.compile(), research_profile=research_profile)


def _is_transient_fetch_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "connection reset" in text
        or "forcibly closed" in text
        or "connection aborted" in text
        or exc.__class__.__name__ in {"ConnectionError", "ChunkedEncodingError"}
    )


def _friendly_fetch_error(message: str) -> str:
    lower = message.lower()
    if "connection reset" in lower or "forcibly closed" in lower or "connection aborted" in lower:
        return "The source server closed the connection while Draftly was fetching it."
    if "timed out" in lower or "timeout" in lower:
        return "The source took too long to respond."
    if "404" in lower:
        return "The source page was not found."
    return "The source could not be fetched."
