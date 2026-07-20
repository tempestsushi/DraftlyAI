from __future__ import annotations

from app.agents import AgentIntent, classify_request


def test_normal_question_routes_to_research_answer() -> None:
    decision = classify_request("How does Jenkins automate deployments?")

    assert decision.intent == AgentIntent.research
    assert "question-style" in decision.reason


def test_explicit_post_request_routes_to_draft_workflow() -> None:
    decision = classify_request("Write a LinkedIn post about CI/CD pipelines")

    assert decision.intent == AgentIntent.linkedin_draft
    assert "draft-writing" in decision.reason


def test_rewrite_request_routes_to_rewrite_workflow() -> None:
    decision = classify_request("Rewrite this draft to sound more concise")

    assert decision.intent == AgentIntent.rewrite
    assert "rewrite" in decision.reason


def test_project_link_request_routes_to_research_answer() -> None:
    decision = classify_request("Summarize this project link")

    assert decision.intent == AgentIntent.research


def test_project_summary_request_routes_to_research_answer() -> None:
    decision = classify_request("Can you summarize this project for me?")

    assert decision.intent == AgentIntent.research


def test_current_event_request_routes_to_research_first() -> None:
    decision = classify_request("What are the latest coding models released this month?")

    assert decision.intent == AgentIntent.research
    assert "current-event" in decision.reason


def test_plain_statement_defaults_to_conversational_research() -> None:
    decision = classify_request("Help me understand Docker networking")

    assert decision.intent == AgentIntent.research
