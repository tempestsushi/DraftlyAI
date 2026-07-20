from __future__ import annotations

from app.agents.search_queries import build_search_query


def test_build_search_query_preserves_user_prompt_wording() -> None:
    prompt = (
        "Can you tell me about EDA (data analysis), what are the stages and how is it useful in finding insights to data?"
    )
    query = build_search_query(prompt)

    assert query == prompt


def test_build_search_query_preserves_freshness_terms() -> None:
    query = build_search_query("What are the latest AI coding models released this year?")

    assert "What are the" in query
    assert "latest" in query
    assert "AI" in query
    assert "coding" in query
    assert "models" in query


def test_build_search_query_uses_context_for_short_follow_up() -> None:
    query = build_search_query(
        "how does it work?",
        conversation_summary="The user is asking about Jenkins CI/CD pipelines.",
        recent_messages=[{"role": "assistant", "content": "Jenkins automates build, test, and deploy steps."}],
    )

    assert "jenkins" in query.lower()
    assert "ci" in query.lower() or "cd" in query.lower()


def test_build_search_query_uses_context_for_clarification_follow_up() -> None:
    query = build_search_query(
        "i meant tools that make frontend through AI",
        recent_messages=[
            {
                "role": "user",
                "content": "Tell me about what tools are being used to make frontend webpages only, which ones are paid and free",
            },
            {
                "role": "assistant",
                "content": "Frontend webpage tools include editors, frameworks, hosting, and design systems.",
            },
        ],
    )

    lowered = query.lower()
    assert "frontend" in lowered
    assert "ai" in lowered
    assert "paid" in lowered
    assert "free" in lowered
    assert "webpages" in lowered
