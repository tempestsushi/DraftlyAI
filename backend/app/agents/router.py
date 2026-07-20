from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class AgentIntent(str, Enum):
    research = "research"
    linkedin_draft = "linkedin_draft"
    rewrite = "rewrite"


GENERIC_URL_RE = re.compile(r"https?://\S+")

REWRITE_KEYWORDS = (
    "rewrite",
    "rephrase",
    "polish",
    "shorten",
    "improve this",
    "make this better",
    "edit this",
    "revise this",
)

REWRITE_PREFIXES = (
    "rewrite this",
    "rewrite the",
    "rephrase this",
    "polish this",
    "shorten this",
    "edit this",
    "revise this",
    "improve this draft",
    "improve this post",
)

CURRENT_EVENT_KEYWORDS = (
    "latest",
    "recent",
    "new",
    "released",
    "current",
    "today",
    "this week",
    "this month",
    "just announced",
    "breaking",
    "news",
    "update",
)

RESEARCH_KEYWORDS = (
    "search",
    "look up",
    "what models",
    "compare",
    "what is",
    "how does",
    "why is",
    "why are",
    "explain",
    "help me understand",
    "tell me about",
    "can you search",
    "can you explain",
)

DRAFT_KEYWORDS = (
    "linkedin draft",
    "linkedin post",
    "write a post",
    "write me a post",
    "create a draft",
    "draft a post",
    "turn this into a post",
    "turn this into a linkedin post",
    "make a post about",
    "caption for linkedin",
)

DRAFT_PREFIXES = (
    "write a post",
    "write me a post",
    "create a draft",
    "draft a post",
    "turn this into a post",
    "turn this into a linkedin post",
    "make a post about",
    "write a linkedin post",
)


@dataclass(slots=True)
class RoutingDecision:
    intent: AgentIntent
    reason: str


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _starts_with_any(text: str, prefixes: tuple[str, ...]) -> bool:
    return any(text.startswith(prefix) for prefix in prefixes)


def _is_question(message: str) -> bool:
    return "?" in message or bool(re.match(r"^(what|how|why|when|where|who|which|can|could|should|is|are|do|does)\b", message))


def classify_request(message: str) -> RoutingDecision:
    text = message.lower().strip()

    if _starts_with_any(text, REWRITE_PREFIXES) or _contains_any(text, REWRITE_KEYWORDS):
        return RoutingDecision(
            intent=AgentIntent.rewrite,
            reason="rewrite keywords detected",
        )

    if _starts_with_any(text, DRAFT_PREFIXES) or _contains_any(text, DRAFT_KEYWORDS):
        return RoutingDecision(
            intent=AgentIntent.linkedin_draft,
            reason="explicit draft-writing request detected",
        )

    if _contains_any(text, CURRENT_EVENT_KEYWORDS):
        return RoutingDecision(
            intent=AgentIntent.research,
            reason="current-event or recent-info request detected",
        )

    if _contains_any(text, RESEARCH_KEYWORDS) or _is_question(text):
        return RoutingDecision(
            intent=AgentIntent.research,
            reason="research or question-style request detected",
        )

    return RoutingDecision(
        intent=AgentIntent.research,
        reason="defaulting to conversational answer workflow",
    )
