from __future__ import annotations

import asyncio
import threading
import time

import pytest

from app.agents import AgentIntent
from app.agents import prompts
from app.agents.graph import AgentGraph, create_chat_model, resolve_research_profile
from app.agents.prompts import ANSWER_SYSTEM_PROMPT
from app.models import DraftLength, DraftTone, MessageRole, ResearchDepth, TopicStatus
from app.services.agent import (
    _build_response_timeout_fallback,
    _friendly_agent_error,
    create_draft_from_topic_response,
    regenerate_draft_from_same_answer,
    stream_agent_run,
)


class FakeGraph:
    def __init__(self):
        self.seen_state = None

    async def astream(self, state, stream_mode="updates"):
        _ = stream_mode
        self.seen_state = dict(state)
        yield {"prepare_query": {"plan": "", "search_query": "jenkins ci cd automation"}}
        yield {
            "search_web": {
                "search_query": "jenkins ci cd automation",
                "search_results": [
                    {
                        "title": "Jenkins docs",
                        "url": "https://www.jenkins.io/doc/",
                        "snippet": "Automation server",
                    }
                ]
            }
        }
        yield {
            "fetch_sources": {
                "fetched_sources": [
                    {
                        "title": "Jenkins docs",
                        "url": "https://www.jenkins.io/doc/",
                        "snippet": "Automation server",
                        "content": "Jenkins automates builds, tests, and deployment pipelines.",
                    }
        ]
            }
        }
        yield {
            "summarize_sources": {
                "source_context": "Jenkins is a CI/CD automation server.",
                "evidence_mode": "extractive",
                "content_selection_debug_log": "Content selection stats:\n- fetched sources: 1\n- selected ideas: 1",
            }
        }


class FakeAgent:
    def __init__(self):
        self.graph = FakeGraph()
        self.summary_calls = 0

    async def stream_response(self, *_args, **_kwargs):
        for chunk in ["Jenkins ", "automates ", "deployment workflows."]:
            yield chunk

    def consume_usage_metadata(self):
        return {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160}

    async def summarize_conversation(self, _previous_summary, _recent_messages):
        self.summary_calls += 1
        return "User asked about Jenkins and automation."

    async def build_draft_from_answer_with_options(self, topic, answer, **_kwargs):
        return f"LinkedIn draft about {topic}: {answer[:40]}"


class TimeoutResponseAgent(FakeAgent):
    async def stream_response(self, *_args, **_kwargs):
        raise asyncio.TimeoutError
        yield


class UsageLessAgent(FakeAgent):
    def consume_usage_metadata(self):
        return None


@pytest.mark.asyncio
async def test_stream_agent_run_persists_answer_and_sources(monkeypatch, test_store) -> None:
    monkeypatch.setattr("app.services.agent.classify_request", lambda topic: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "test route",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: FakeAgent())

    events = [event async for event in stream_agent_run(test_store, "What is Jenkins?", research_depth=ResearchDepth.quick)]

    assert any("event: done" in event for event in events)
    topics = test_store.list_topics()
    assert len(topics) == 1
    saved_topic = topics[0]
    assert saved_topic.status == TopicStatus.complete
    assert "Jenkins automates deployment workflows." in (saved_topic.response_content or "")

    messages = test_store.list_messages(saved_topic.id)
    assert [message.role for message in messages] == [MessageRole.user, MessageRole.assistant]

    sources = test_store.list_message_sources(saved_topic.id)
    assert len(sources) == 1
    assert sources[0].domain == "jenkins.io"
    logs = test_store.list_logs()
    assert any("Candidate sources:" in log.message for log in logs)
    assert any("Jenkins docs | jenkins.io" in log.message for log in logs)
    assert any("Fetched source detail:" in log.message for log in logs)
    assert any("page extract" in log.message for log in logs)
    assert any("Extractive source evidence prepared" in log.message for log in logs)
    assert any("Content selection stats:" in log.message for log in logs)
    assert any("Gemini usage: input=120, output=40, total=160" in log.message for log in logs)


@pytest.mark.asyncio
async def test_stream_agent_run_passes_follow_up_memory_into_research_state(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("Jenkins", TopicStatus.complete)
    test_store.add_message(topic.id, MessageRole.user, "Explain Jenkins.")
    test_store.add_message(topic.id, MessageRole.assistant, "Jenkins is a CI/CD automation server.")
    test_store.update_topic_response(
        topic.id,
        response_content="Jenkins is a CI/CD automation server.",
        conversation_summary="User wants practical CI/CD explanations.",
        status=TopicStatus.complete,
    )

    fake_agent = FakeAgent()
    monkeypatch.setattr("app.services.agent.classify_request", lambda message: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "follow-up test",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: fake_agent)

    _ = [event async for event in stream_agent_run(test_store, "How does it automate deployments?", topic_id=topic.id)]

    assert fake_agent.graph.seen_state is not None
    assert fake_agent.graph.seen_state["conversation_summary"] == "User wants practical CI/CD explanations."
    recent_messages = fake_agent.graph.seen_state["recent_messages"]
    assert any("Explain Jenkins." in message["content"] for message in recent_messages)
    assert any("How does it automate deployments?" in message["content"] for message in recent_messages)


@pytest.mark.asyncio
async def test_stream_agent_run_passes_prior_sources_into_follow_up_state(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("Project article", TopicStatus.complete)
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "This project uses a Kanban workflow.")
    test_store.add_message_sources(
        topic.id,
        assistant.id,
        [
            {
                "title": "GitHub repository: tempestsushi/KanbanKaii",
                "url": "https://github.com/tempestsushi/KanbanKaii",
                "domain": "github.com",
                "snippet": "README source",
            }
        ],
    )
    fake_agent = FakeAgent()
    monkeypatch.setattr("app.services.agent.classify_request", lambda message: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "follow-up source test",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: fake_agent)

    _ = [event async for event in stream_agent_run(test_store, "Make it more concise.", topic_id=topic.id)]

    assert fake_agent.graph.seen_state is not None
    assert fake_agent.graph.seen_state["prior_sources"] == [
        {
            "title": "GitHub repository: tempestsushi/KanbanKaii",
            "url": "https://github.com/tempestsushi/KanbanKaii",
            "snippet": "README source",
            "domain": "github.com",
        }
    ]


@pytest.mark.asyncio
async def test_quick_mode_skips_conversation_summary_update(monkeypatch, test_store) -> None:
    fake_agent = FakeAgent()
    monkeypatch.setattr("app.services.agent.classify_request", lambda topic: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "test route",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda **kwargs: fake_agent)

    _ = [event async for event in stream_agent_run(test_store, "What is Jenkins?", research_depth=ResearchDepth.quick)]

    assert fake_agent.summary_calls == 0
    assert any("Quick mode skipped conversation summary update" in log.message for log in test_store.list_logs())


@pytest.mark.asyncio
async def test_moderate_mode_updates_conversation_summary(monkeypatch, test_store) -> None:
    fake_agent = FakeAgent()
    monkeypatch.setattr("app.services.agent.classify_request", lambda topic: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "test route",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda **kwargs: fake_agent)

    _ = [event async for event in stream_agent_run(test_store, "What is Jenkins?", research_depth=ResearchDepth.moderate)]

    assert fake_agent.summary_calls == 1
    assert test_store.list_topics()[0].conversation_summary == "User asked about Jenkins and automation."


@pytest.mark.asyncio
async def test_stream_agent_run_returns_error_done_payload(monkeypatch, test_store) -> None:
    class BrokenGraph:
        async def astream(self, state, stream_mode="updates"):
            _ = state, stream_mode
            raise TimeoutError("search timed out")
            yield

    class BrokenAgent:
        def __init__(self):
            self.graph = BrokenGraph()

    monkeypatch.setattr("app.services.agent.classify_request", lambda message: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "broken test",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: BrokenAgent())

    events = [event async for event in stream_agent_run(test_store, "Explain Jenkins")]

    assert any('"state": "error"' in event for event in events)
    assert any("request timed out" in event for event in events)
    saved_topic = test_store.list_topics()[0]
    assert saved_topic.status == TopicStatus.error


@pytest.mark.asyncio
async def test_stream_agent_run_regenerates_from_selected_assistant_message(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("Jenkins", TopicStatus.complete)
    test_store.add_message(topic.id, MessageRole.user, "Explain Jenkins.")
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "Old answer")
    fake_agent = FakeAgent()

    monkeypatch.setattr("app.services.agent.classify_request", lambda message: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "regenerate test",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda **kwargs: fake_agent)

    events = [
        event
        async for event in stream_agent_run(
            test_store,
            "Regenerate answer",
            topic_id=topic.id,
            regenerate_message_id=assistant.id,
            research_depth=ResearchDepth.quick,
        )
    ]

    assert any("event: done" in event for event in events)
    assert fake_agent.graph.seen_state is not None
    assert fake_agent.graph.seen_state["topic"] == "Explain Jenkins."
    user_messages = [message for message in test_store.list_messages(topic.id) if message.role == MessageRole.user]
    assistant_messages = [message for message in test_store.list_messages(topic.id) if message.role == MessageRole.assistant]
    assert len(user_messages) == 1
    assert len(assistant_messages) == 2
    assert any("Regenerating answer" in log.message for log in test_store.list_logs())


def test_friendly_agent_error_messages_are_provider_specific() -> None:
    assert "Tavily search failed" in _friendly_agent_error(RuntimeError("Tavily search failed with 401"))
    assert "Gemini could not complete" in _friendly_agent_error(RuntimeError("Google Gemini quota exceeded"))
    assert "timed out" in _friendly_agent_error(asyncio.TimeoutError())


@pytest.mark.asyncio
async def test_stream_agent_run_prepares_query_without_planning_log(monkeypatch, test_store) -> None:
    class PrepareQueryGraph:
        async def astream(self, state, stream_mode="updates"):
            _ = stream_mode
            yield {
                "prepare_query": {
                    "plan": "",
                    "search_query": state["topic"],
                }
            }
            yield {
                "search_web": {
                    "search_query": state["topic"],
                    "search_results": [],
                }
            }
            yield {"fetch_sources": {"fetched_sources": []}}
            yield {"summarize_sources": {"source_context": "No external source context could be selected."}}

    class PrepareQueryAgent(FakeAgent):
        def __init__(self):
            self.summary_calls = 0
            self.graph = PrepareQueryGraph()

    monkeypatch.setattr("app.services.agent.classify_request", lambda message: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "prepare query test",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: PrepareQueryAgent())

    events = [event async for event in stream_agent_run(test_store, "Explain Jenkins")]

    assert any("event: done" in event for event in events)
    logs = test_store.list_logs()
    assert any("Search query prepared" in log.message for log in logs)
    assert not any("Planning answer" in log.message for log in logs)
    saved_topic = test_store.list_topics()[0]
    assert saved_topic.status == TopicStatus.complete


def test_resolve_research_profile_distinguishes_depths() -> None:
    quick = resolve_research_profile(ResearchDepth.quick)
    moderate = resolve_research_profile(ResearchDepth.moderate)
    deep = resolve_research_profile(ResearchDepth.deep)

    assert quick.search_max_results < moderate.search_max_results <= deep.search_max_results
    assert quick.fetch_max_sources < moderate.fetch_max_sources < deep.fetch_max_sources
    assert quick.extract_char_limit < moderate.extract_char_limit < deep.extract_char_limit
    assert quick.fetch_max_sources == 1
    assert moderate.fetch_max_sources == 2
    assert deep.fetch_max_sources == 4
    assert quick.search_max_results == 3
    assert moderate.search_max_results == 4
    assert deep.search_max_results == 4
    assert quick.fetch_enabled is False
    assert moderate.fetch_enabled is True
    assert deep.fetch_enabled is True
    assert quick.min_thinking_seconds == 0
    assert moderate.min_thinking_seconds == 0
    assert deep.min_thinking_seconds == 0
    assert quick.max_thinking_seconds == 45
    assert moderate.max_thinking_seconds == 75
    assert deep.max_thinking_seconds == 120
    assert quick.source_context_token_budget < moderate.source_context_token_budget < deep.source_context_token_budget
    assert quick.source_context_token_budget == 300
    assert moderate.source_context_token_budget == 600
    assert deep.source_context_token_budget == 900
    assert quick.gemini_output_tokens == 700
    assert moderate.gemini_output_tokens == 1100
    assert deep.gemini_output_tokens == 1600
    assert quick.answer_word_target == 200
    assert moderate.answer_word_target == 350
    assert deep.answer_word_target == 500
    assert quick.search_query_count == 1
    assert moderate.search_query_count == 2
    assert deep.search_query_count == 3
    assert quick.source_context_idea_target == 1
    assert moderate.source_context_idea_target == 3
    assert deep.source_context_idea_target == 5
    assert quick.rag_top_k < moderate.rag_top_k < deep.rag_top_k
    assert quick.rag_top_k == 1
    assert moderate.rag_top_k == 2
    assert deep.rag_top_k == 3
    assert quick.rag_chunk_size < moderate.rag_chunk_size < deep.rag_chunk_size
    assert quick.rag_chunk_overlap < moderate.rag_chunk_overlap < deep.rag_chunk_overlap
    assert quick.rag_source_char_limit < moderate.rag_source_char_limit < deep.rag_source_char_limit


def test_response_chunk_timeout_uses_depth_window() -> None:
    agent = AgentGraph(
        llm=object(),
        graph=None,
        research_profile=resolve_research_profile(ResearchDepth.deep),
    )

    assert agent._response_chunk_timeout() == 120


def test_depth_window_does_not_expand_utility_llm_timeouts() -> None:
    agent = AgentGraph(
        llm=object(),
        graph=None,
        research_profile=resolve_research_profile(ResearchDepth.deep),
    )

    assert agent._timeout_with_depth(25) == 25


def test_answer_prompt_and_memory_context_stay_compact() -> None:
    assert len(ANSWER_SYSTEM_PROMPT.split()) <= 120

    messages = [
        {"role": "user", "content": f"user message {index} " + ("x" * 500)}
        if index % 2
        else {"role": "assistant", "content": f"assistant answer {index} " + ("y" * 900)}
        for index in range(8)
    ]
    context = AgentGraph(llm=object(), graph=None)._conversation_context_block(
        "summary " + ("z" * 900),
        messages,
    )

    assert len(context) < 2200
    assert "user message 1" not in context
    assert "assistant answer 0" not in context
    assert "user message 7" in context


def test_all_agent_system_prompts_stay_under_120_words() -> None:
    prompt_values = {
        name: value
        for name, value in vars(prompts).items()
        if name.endswith("_PROMPT") and isinstance(value, str)
    }

    assert prompt_values
    for name, value in prompt_values.items():
        assert len(value.split()) <= 120, name


def test_create_chat_model_requires_gemini_key(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.graph.llms.settings.model_provider", "gemini")
    monkeypatch.setattr("app.agents.graph.llms.settings.gemini_api_key", None)

    try:
        create_chat_model()
    except RuntimeError as exc:
        assert "GEMINI_API_KEY" in str(exc) or "langchain-google-genai" in str(exc)
    else:
        raise AssertionError("Expected Gemini provider without key to raise RuntimeError")


def test_build_search_query_variants_uses_depth_count_and_freshness_terms() -> None:
    variants = AgentGraph.build_search_query_variants(
        "What are the latest AI coding models?",
        "latest AI coding models",
        3,
    )

    assert len(variants) == 3
    assert variants[0] == "latest AI coding models"
    assert any("official sources" in variant or "latest news" in variant or "recent articles" in variant for variant in variants)


def test_rank_search_results_prefers_more_relevant_and_authoritative_sources() -> None:
    ranked = AgentGraph.rank_search_results(
        "Jenkins CI/CD deployment",
        [
            {"title": "Random blog", "url": "https://example.com/post", "snippet": "general software thoughts"},
            {"title": "Jenkins documentation", "url": "https://www.jenkins.io/doc/", "snippet": "Jenkins CI/CD deployment docs"},
            {"title": "Deployment pipelines", "url": "https://developer.example.com/pipelines", "snippet": "CI/CD deployment guide"},
        ],
    )

    assert ranked[0]["url"] == "https://www.jenkins.io/doc/"


def test_rank_search_results_prefers_latest_release_sources_over_generic_what_is_pages() -> None:
    ranked = AgentGraph.rank_search_results(
        "latest OpenAI coding models",
        [
            {
                "title": "What is an AI coding model?",
                "url": "https://example-tutorials.com/what-is-ai-coding-model",
                "snippet": "A beginner explanation from 2021 about coding assistants.",
            },
            {
                "title": "OpenAI model release notes 2026",
                "url": "https://openai.com/release-notes/coding-models",
                "snippet": "Latest release notes for OpenAI coding models and developer tools in 2026.",
            },
            {
                "title": "Top 25 AI Coding Tools",
                "url": "https://medium.com/random-blog/top-ai-coding-tools",
                "snippet": "A listicle about coding tools.",
            },
        ],
    )

    assert ranked[0]["url"] == "https://openai.com/release-notes/coding-models"


def test_rank_search_results_filters_social_and_prefers_topic_matched_official_sources() -> None:
    ranked = AgentGraph.rank_search_results(
        "latest Nike campaign performance marketing strategy",
        [
            {
                "title": "Nike campaign discussion",
                "url": "https://www.reddit.com/r/marketing/comments/example",
                "snippet": "People discuss Nike marketing strategy.",
            },
            {
                "title": "Nike Newsroom: Latest Campaign",
                "url": "https://news.nike.com/campaign/latest-performance-marketing",
                "snippet": "Official Nike newsroom article about the latest performance marketing campaign.",
            },
            {
                "title": "Top 10 sports campaigns",
                "url": "https://random-marketing-blog.example.com/top-sports-campaigns",
                "snippet": "A third-party listicle about sports marketing campaigns.",
            },
            {
                "title": "Marketing industry campaign analysis",
                "url": "https://example.org/reports/campaign-analysis",
                "snippet": "A nonprofit report discussing campaign performance trends.",
            },
        ],
    )

    assert ranked[0]["url"] == "https://news.nike.com/campaign/latest-performance-marketing"
    assert all("reddit.com" not in result["url"] for result in ranked)


def test_rank_search_results_limits_duplicate_domains() -> None:
    ranked = AgentGraph.rank_search_results(
        "Python async documentation",
        [
            {
                "title": "Python async docs",
                "url": "https://docs.python.org/3/library/asyncio.html",
                "snippet": "Official Python asyncio documentation.",
            },
            {
                "title": "Python async tasks",
                "url": "https://docs.python.org/3/library/asyncio-task.html",
                "snippet": "Official Python asyncio task documentation.",
            },
            {
                "title": "Python async event loop",
                "url": "https://docs.python.org/3/library/asyncio-eventloop.html",
                "snippet": "Official Python event loop documentation.",
            },
            {
                "title": "Async Python examples",
                "url": "https://realpython.com/async-io-python/",
                "snippet": "Text article with Python async examples.",
            },
        ],
    )

    docs_results = [result for result in ranked if "docs.python.org" in result["url"]]
    assert len(docs_results) == 2
    assert any("realpython.com" in result["url"] for result in ranked)


@pytest.mark.asyncio
async def test_fetch_node_fetches_sources_in_parallel(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    results = [
        {
            "title": f"Source {index}",
            "url": f"https://example{index}.com/docs",
            "snippet": "This source has a detailed snippet about Python async documentation and practical implementation guidance.",
        }
        for index in range(5)
    ]
    active = 0
    max_active = 0
    lock = threading.Lock()

    async def fake_summarize_sources(self, _topic, _fetched_sources):
        return "Summary"

    async def fail_build_plan(self, *_args, **_kwargs):
        raise AssertionError("build_plan should not run for normal research answers")

    def fake_search_web(*_args, **_kwargs):
        return results

    def fake_fetch_source_content(url, **_kwargs):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        try:
            time.sleep(0.2)
            return {
                "url": url,
                "content": " ".join(["Detailed extracted source content about Python async documentation."] * 12),
            }
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(AgentGraph, "build_plan", fail_build_plan)
    monkeypatch.setattr(AgentGraph, "summarize_sources", fake_summarize_sources)
    monkeypatch.setattr(AgentGraph, "build_search_query_variants", staticmethod(lambda topic, primary_query, count: ["query"]))
    monkeypatch.setattr(workflow_module, "build_search_query", lambda *args, **kwargs: "python async documentation")
    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.deep)
    started_at = time.perf_counter()
    updates = [
        update
        async for update in agent.graph.astream(
            {"topic": "Python async documentation", "recent_messages": [], "conversation_summary": ""},
            stream_mode="updates",
        )
    ]
    elapsed = time.perf_counter() - started_at
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert len(fetch_update["fetched_sources"]) == 4
    assert max_active >= 3
    assert elapsed < 0.7


@pytest.mark.asyncio
async def test_fetch_node_backfills_failed_fetches_with_snippets(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    results = [
        {
            "title": f"Source {index}",
            "url": f"https://example{index}.com/docs",
            "snippet": (
                "This source has a detailed snippet about Gemini model parameters, supported media types, "
                "token limits, and practical API configuration details."
            ),
        }
        for index in range(3)
    ]

    def fake_search_web(*_args, **_kwargs):
        return results

    def flaky_fetch_source_content(url, **_kwargs):
        if "example0" not in url:
            raise TimeoutError("fetch failed")
        return {
            "content": " ".join(
                ["Gemini model parameters include temperature, topP, topK, and output token limits."] * 8
            )
        }

    monkeypatch.setattr(AgentGraph, "build_search_query_variants", staticmethod(lambda topic, primary_query, count: ["query"]))
    monkeypatch.setattr(workflow_module, "build_search_query", lambda *args, **kwargs: "gemini model parameters")
    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", flaky_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.moderate)
    updates = [
        update
        async for update in agent.graph.astream(
            {"topic": "Gemini model parameters and supported media types", "recent_messages": [], "conversation_summary": ""},
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert len(fetch_update["fetched_sources"]) == 2
    assert fetch_update["fetched_sources"][0]["content"]
    assert any(source["content"] == "" for source in fetch_update["fetched_sources"][1:])


@pytest.mark.asyncio
async def test_fetch_node_replaces_weak_extracts_with_later_strong_sources(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    results = [
            {
                "title": "Weak source",
                "url": "https://weak-source.com/article",
                "snippet": "A relevant but thin snippet about cultural anthropology and marketing response prediction.",
            },
            {
                "title": "Strong source one",
                "url": "https://strong-one.com/article",
                "snippet": "A relevant article about cultural anthropology and marketing research.",
            },
            {
                "title": "Strong source two",
                "url": "https://strong-two.com/article",
                "snippet": "A relevant article about demographics, cultural meaning, and marketing messages.",
            },
    ]

    def fake_search_web(*_args, **_kwargs):
        return results

    def fake_fetch_source_content(url, **_kwargs):
        if "weak" in url:
            return {"content": "Thin extract about anthropology."}
        return {
            "content": " ".join(
                [
                    "Cultural anthropology studies shared meanings, practices, rituals, and social context that shape how people interpret marketing messages."
                ]
                * 8
            )
        }

    monkeypatch.setattr(AgentGraph, "build_search_query_variants", staticmethod(lambda topic, primary_query, count: ["query"]))
    monkeypatch.setattr(workflow_module, "build_search_query", lambda *args, **kwargs: "cultural anthropology marketing")
    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.moderate)
    updates = [
        update
        async for update in agent.graph.astream(
            {"topic": "cultural anthropology marketing response", "recent_messages": [], "conversation_summary": ""},
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    urls = [source["url"] for source in fetch_update["fetched_sources"]]
    assert urls == [
        "https://strong-one.com/article",
        "https://strong-two.com/article",
    ]


@pytest.mark.asyncio
async def test_quick_depth_uses_snippet_without_fetch_when_snippet_is_strong(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    def fake_search_web(*_args, **_kwargs):
        return [
            {
                "title": "Jenkins docs",
                "url": "https://www.jenkins.io/doc/",
                "snippet": "Jenkins is an automation server that supports building, testing, and deploying software through CI/CD pipelines with plugins and repeatable workflows.",
            }
        ]

    def fail_fetch_source_content(*_args, **_kwargs):
        raise AssertionError("quick mode should use strong Tavily snippets without fetching full pages")

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fail_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.quick)
    updates = [
        update
        async for update in agent.graph.astream(
            {"topic": "What is Jenkins?", "recent_messages": [], "conversation_summary": ""},
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert len(fetch_update["fetched_sources"]) == 1
    assert fetch_update["fetched_sources"][0]["content"] == ""


@pytest.mark.asyncio
async def test_quick_depth_fetches_when_snippet_is_weak(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetch_count = 0

    def fake_search_web(*_args, **_kwargs):
        return [{"title": "Jenkins docs", "url": "https://www.jenkins.io/doc/", "snippet": "Jenkins docs."}]

    def fake_fetch_source_content(*_args, **_kwargs):
        nonlocal fetch_count
        fetch_count += 1
        return {
            "content": " ".join(
                ["Jenkins automates software build, test, and deployment workflows for CI/CD pipelines."] * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.quick)
    updates = [
        update
        async for update in agent.graph.astream(
            {"topic": "What is Jenkins?", "recent_messages": [], "conversation_summary": ""},
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert fetch_count == 1
    assert len(fetch_update["fetched_sources"]) == 1
    assert "Jenkins automates" in fetch_update["fetched_sources"][0]["content"]


@pytest.mark.asyncio
async def test_prompt_url_is_fetched_before_search_results(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetched_urls: list[str] = []

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("URL prompts should not run web search")

    def fake_fetch_source_content(url, **_kwargs):
        fetched_urls.append(url)
        return {
            "content": " ".join(
                ["This article explains the exact example article content and its practical meaning."] * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.moderate)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": "Explain this article: https://example.com/article",
                "recent_messages": [],
                "conversation_summary": "",
            },
            stream_mode="updates",
        )
    ]
    search_update = next(update["search_web"] for update in updates if "search_web" in update)
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert search_update["search_results"][0]["url"] == "https://example.com/article"
    assert fetched_urls[0] == "https://example.com/article"
    assert fetch_update["fetched_sources"][0]["url"] == "https://example.com/article"


@pytest.mark.asyncio
async def test_url_fetch_retries_connection_reset(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetch_count = 0

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("URL prompts should not run web search")

    def flaky_fetch_source_content(*_args, **_kwargs):
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 1:
            raise ConnectionError(
                "('Connection aborted.', ConnectionResetError(10054, "
                "'An existing connection was forcibly closed by the remote host', None, 10054, None))"
            )
        return {
            "content": " ".join(
                ["This article explains the recovered page content after a retry."] * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", flaky_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.moderate)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": "Explain this article: https://example.com/article",
                "recent_messages": [],
                "conversation_summary": "",
            },
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert fetch_count == 2
    assert "recovered page content" in fetch_update["fetched_sources"][0]["content"]


@pytest.mark.asyncio
async def test_article_url_fetch_uses_general_fallback_variants(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetched_urls: list[str] = []

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("URL prompts should not run web search")

    def fake_fetch_source_content(url, **_kwargs):
        fetched_urls.append(url)
        if url != "https://example.com/article/":
            raise ValueError("temporary fetch failure")
        return {
            "content": " ".join(
                ["The article fallback variant contains enough useful extracted information."] * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.moderate)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": "Explain this article: https://example.com/article",
                "recent_messages": [],
                "conversation_summary": "",
            },
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert fetched_urls[:2] == ["https://example.com/article", "https://example.com/article/"]
    assert "fallback variant" in fetch_update["fetched_sources"][0]["content"]


@pytest.mark.asyncio
async def test_github_repo_url_fetches_raw_readme(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetched_urls: list[str] = []

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("GitHub URL prompts should not run web search")

    def fake_fetch_source_content(url, **_kwargs):
        fetched_urls.append(url)
        return {
            "content": " ".join(
                [
                    "KanbanKaii is a kanban project management app with boards, columns, tasks, and drag-and-drop workflow features."
                ]
                * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.quick)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": (
                    "https://github.com/tempestsushi/KanbanKaii, make a draft about this project "
                    "and its functioning, how i made it, keep it concise and point out useful README information"
                ),
                "recent_messages": [],
                "conversation_summary": "",
            },
            stream_mode="updates",
        )
    ]
    search_update = next(update["search_web"] for update in updates if "search_web" in update)
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert search_update["search_results"][0]["title"] == "GitHub repository: tempestsushi/KanbanKaii"
    assert fetched_urls == ["https://raw.githubusercontent.com/tempestsushi/KanbanKaii/main/README.md"]
    assert "KanbanKaii" in fetch_update["fetched_sources"][0]["content"]


@pytest.mark.asyncio
async def test_github_repo_url_falls_back_to_master_readme(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetched_urls: list[str] = []

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("GitHub URL prompts should not run web search")

    def fake_fetch_source_content(url, **_kwargs):
        fetched_urls.append(url)
        if "/main/README.md" in url:
            raise ValueError("404 Client Error")
        return {
            "content": " ".join(
                ["The repository README was found on the master branch and explains the app."] * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.quick)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": "Explain https://github.com/tempestsushi/KanbanKaii",
                "recent_messages": [],
                "conversation_summary": "",
            },
            stream_mode="updates",
        )
    ]
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert fetched_urls[:2] == [
        "https://raw.githubusercontent.com/tempestsushi/KanbanKaii/main/README.md",
        "https://raw.githubusercontent.com/tempestsushi/KanbanKaii/master/README.md",
    ]
    assert "master branch" in fetch_update["fetched_sources"][0]["content"]


@pytest.mark.asyncio
async def test_follow_up_reuses_prior_source_url_without_search(monkeypatch) -> None:
    import app.agents.graph.workflow as workflow_module
    from app.agents.graph import create_agent_graph

    fetched_urls: list[str] = []

    def fake_search_web(*_args, **_kwargs):
        raise AssertionError("Follow-up with prior sources should not run web search")

    def fake_fetch_source_content(url, **_kwargs):
        fetched_urls.append(url)
        return {
            "content": " ".join(
                [
                    "KanbanKaii is a kanban project management app with boards, columns, tasks, and drag-and-drop workflow features."
                ]
                * 8
            )
        }

    monkeypatch.setattr(workflow_module, "search_web", fake_search_web)
    monkeypatch.setattr(workflow_module, "fetch_source_content", fake_fetch_source_content)
    monkeypatch.setattr(workflow_module.settings, "model_provider", "ollama")

    agent = create_agent_graph(research_depth=ResearchDepth.quick)
    updates = [
        update
        async for update in agent.graph.astream(
            {
                "topic": "Now make it more concise and focus on how I built it.",
                "recent_messages": [],
                "conversation_summary": "The chat is about the KanbanKaii GitHub project.",
                "prior_sources": [
                    {
                        "title": "GitHub repository: tempestsushi/KanbanKaii",
                        "url": "https://github.com/tempestsushi/KanbanKaii",
                        "snippet": "Previously used README source.",
                    }
                ],
            },
            stream_mode="updates",
        )
    ]
    search_update = next(update["search_web"] for update in updates if "search_web" in update)
    fetch_update = next(update["fetch_sources"] for update in updates if "fetch_sources" in update)

    assert search_update["search_results"][0]["url"] == "https://github.com/tempestsushi/KanbanKaii"
    assert fetched_urls == ["https://raw.githubusercontent.com/tempestsushi/KanbanKaii/main/README.md"]
    assert "KanbanKaii" in fetch_update["fetched_sources"][0]["content"]


def test_extractive_source_context_preserves_selected_evidence() -> None:
    summary = AgentGraph.build_extractive_source_context_text(
        "What is Jenkins?",
        [
            {
                "title": "Jenkins documentation",
                "url": "https://www.jenkins.io/doc/",
                "snippet": "Jenkins is an automation server.",
                "content": "It automates software build, test, and deployment workflows.",
            }
        ],
    )

    assert "Evidence for:" in summary
    assert "Jenkins documentation" in summary
    assert "automation server" in summary


def test_extractive_source_context_balances_evidence_between_sources() -> None:
    summary = AgentGraph.build_extractive_source_context_text(
        "How is AI changing digital marketing?",
        [
            {
                "title": "Long marketing report",
                "url": "https://example.com/long",
                "snippet": "AI is changing digital marketing workflows.",
                "content": " ".join(
                    [
                        "AI helps marketing teams create content, personalize campaigns, analyze audiences, and test creative performance."
                    ]
                    * 20
                ),
            },
            {
                "title": "Short marketing article",
                "url": "https://example.com/short",
                "snippet": "Marketers use AI to draft social posts, segment users, and improve campaign timing.",
                "content": "AI can support faster content production while humans still guide strategy and brand voice.",
            },
        ],
        source_context_token_budget=360,
    )

    assert "Long marketing report" in summary
    assert "Short marketing article" in summary
    assert "segment users" in summary
    assert summary.count("[Idea") == 2


@pytest.mark.asyncio
async def test_summarize_sources_uses_local_evidence_without_llm_call() -> None:
    class ExplodingLlm:
        async def ainvoke(self, _messages):
            raise AssertionError("summarize_sources should not call the LLM")

    agent = AgentGraph(llm=ExplodingLlm(), graph=None)

    summary = await agent.summarize_sources(
        "What is Jenkins?",
        [
            {
                "title": "Jenkins documentation",
                "url": "https://www.jenkins.io/doc/",
                "snippet": "Jenkins is an automation server.",
                "content": "It automates software delivery pipelines.",
            }
        ],
    )

    assert "Evidence for:" in summary
    assert "Jenkins documentation" in summary


@pytest.mark.asyncio
async def test_summarize_sources_uses_rag_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.graph.helper.settings.rag_enabled", True)
    monkeypatch.setattr("app.agents.graph.helper.settings.rag_provider", "local")
    monkeypatch.setattr("app.agents.graph.helper.settings.rag_embed_model", "")

    agent = AgentGraph(
        llm=object(),
        graph=None,
        research_profile=resolve_research_profile(ResearchDepth.moderate),
    )

    summary = await agent.summarize_sources(
        "How does tokenization work inside an AI model?",
        [
            {
                "title": "Tokenization guide",
                "url": "https://example.com/tokenization",
                "snippet": "Tokenization splits text into tokens.",
                "content": (
                    "Tokenization breaks text into smaller tokens such as words, subwords, or characters. "
                    "The tokenizer maps each token to an integer id before the model processes it."
                ),
            },
            {
                "title": "Unrelated article",
                "url": "https://example.com/unrelated",
                "snippet": "A short unrelated article.",
                "content": "This page discusses office furniture and room layouts.",
            },
        ],
    )

    debug_log = agent.consume_content_selection_debug_log()

    assert "Evidence for:" in summary
    assert "Tokenization guide" in summary
    assert "RAG retrieval stats:" in debug_log
    assert "provider: local" in debug_log
    assert "top k: 2" in debug_log


@pytest.mark.asyncio
async def test_stream_agent_run_saves_fallback_when_final_response_times_out(monkeypatch, test_store) -> None:
    monkeypatch.setattr("app.services.agent.classify_request", lambda topic: type("Decision", (), {
        "intent": AgentIntent.research,
        "reason": "test route",
    })())
    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda research_depth=None: TimeoutResponseAgent())

    events = [event async for event in stream_agent_run(test_store, "What is Jenkins?", research_depth=ResearchDepth.quick)]

    assert any("event: done" in event for event in events)
    assert any("Final answer stream timed out" in event for event in events)
    saved_topic = test_store.list_topics()[0]
    assert saved_topic.status == TopicStatus.complete
    assert saved_topic.response_content
    assert "local model" not in (saved_topic.response_content or "")
    assert "Research Summary" not in (saved_topic.response_content or "")


def test_response_timeout_fallback_summarizes_ml_topic_like_normal_answer() -> None:
    response = _build_response_timeout_fallback(
        (
            "Research notes\n"
            "1. AWS\n"
            "Key detail: Supervised learning algorithms train on sample data that specifies both input and output. "
            "Unsupervised learning algorithms train on unlabeled data to find patterns. "
            "Linear regression predicts a continuous value."
        ),
    )

    assert "Supervised learning algorithms train on sample data" in response
    assert "Unsupervised learning algorithms train on unlabeled data" in response
    assert "Linear regression predicts a continuous value" in response
    assert "local model" not in response
    assert "Research Summary" not in response


@pytest.mark.asyncio
async def test_create_draft_from_topic_response_reuses_existing_draft(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("LangChain", TopicStatus.complete)
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "LangChain helps compose LLM workflows.")
    existing = test_store.add_draft(
        title="Existing draft",
        content="Already generated",
        source="research",
        topic_id=topic.id,
        source_message_id=assistant.id,
    )

    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda **kwargs: FakeAgent())

    draft = await create_draft_from_topic_response(
        test_store,
        topic.id,
        message_id=assistant.id,
        tone=DraftTone.casual,
        length=DraftLength.short,
        include_cta=False,
        include_hashtags=False,
    )

    assert draft.id == existing.id


@pytest.mark.asyncio
async def test_create_draft_from_topic_response_builds_new_draft(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("LangGraph", TopicStatus.complete)
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "LangGraph manages graph-based agent state.")
    captured_kwargs = {}

    def fake_create_agent_graph(**kwargs):
        captured_kwargs.update(kwargs)
        return FakeAgent()

    monkeypatch.setattr("app.services.agent.create_agent_graph", fake_create_agent_graph)

    draft = await create_draft_from_topic_response(
        test_store,
        topic.id,
        title="LangGraph post",
        message_id=assistant.id,
        tone=DraftTone.thought_leadership,
        length=DraftLength.long,
        include_cta=True,
        include_hashtags=True,
    )

    assert draft.title == "LangGraph post"
    assert draft.topic_id == topic.id
    assert draft.source_message_id == assistant.id
    assert "LinkedIn draft about LangGraph" in draft.content
    assert captured_kwargs["max_output_tokens"] == 1400


@pytest.mark.asyncio
async def test_regenerate_draft_falls_back_to_latest_assistant_message(monkeypatch, test_store) -> None:
    topic = test_store.create_topic("Tokenization", TopicStatus.review)
    test_store.add_message(topic.id, MessageRole.user, "Explain tokenization")
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "Tokenization turns text into token ids.")
    draft = test_store.add_draft(
        title="Old tokenization draft",
        content="Old draft",
        source="research",
        topic_id=topic.id,
        source_message_id=None,
    )

    monkeypatch.setattr("app.services.agent.create_agent_graph", lambda **_kwargs: FakeAgent())

    updated = await regenerate_draft_from_same_answer(
        test_store,
        draft.id,
        tone=DraftTone.professional,
        length=DraftLength.medium,
        include_cta=True,
        include_hashtags=True,
    )

    assert updated.id == draft.id
    assert assistant.content[:40] in updated.content
    versions = test_store.list_draft_versions(draft.id)
    assert versions[0].reason == "regenerated"


def test_compact_answer_for_draft_reduces_long_answer() -> None:
    answer = "\n\n".join(
        [
            "Tokenization breaks raw text into tokens so a model can process it mathematically.",
            "The tokenizer maps tokens into integer IDs before those IDs are converted into vectors.",
            "This matters because the context window is measured in tokens, not words.",
            "Extra paragraph " + ("with repeated detail " * 40),
            "- Supervised learning uses labeled data.",
            "- Unsupervised learning uses unlabeled data.",
        ]
    )

    compact = AgentGraph._compact_answer_for_draft(answer, length=DraftLength.short)

    assert len(compact) < len(answer)
    assert len(compact) <= 720
    assert "Tokenization breaks raw text" in compact
    assert "integer IDs" in compact


def test_compact_answer_for_draft_keeps_later_priority_sections() -> None:
    answer = """
    AI-powered frontend development tools generally fall into two categories: AI coding assistants that help developers write code faster, and generative UI builders that create entire interfaces from text prompts.

    1. AI Coding Assistants
    These tools integrate directly into your code editor like VS Code.
    Top tools: GitHub Copilot and Tabnine are the industry standards.
    Pricing: Typically subscription-based, around $10-$20/month for individuals.

    2. Generative UI Builders
    These tools allow you to describe a webpage in plain English, and the AI generates the HTML, CSS, and JavaScript for you.
    Top tools: v0.dev by Vercel and Bolt.new are currently leading this space.
    Pricing: Most offer a freemium model with paid tiers for higher usage.

    Which should you choose?
    If you are a developer, use coding assistants. If you want to build quickly without deep coding knowledge, use generative builders.

    A note on trade-offs: AI-generated code can be bloated or contain subtle bugs, so you still need review and debugging.
    """

    compact = AgentGraph._compact_answer_for_draft(answer, length=DraftLength.medium)

    assert "AI Coding Assistants" in compact
    assert "Generative UI Builders" in compact
    assert "v0.dev" in compact
    assert "Bolt.new" in compact
    assert "freemium" in compact
    assert "trade-offs" in compact
