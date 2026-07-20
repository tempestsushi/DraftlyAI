from __future__ import annotations

import re

FRESHNESS_TERMS = {
    "latest",
    "new",
    "recent",
    "current",
    "released",
    "release",
    "today",
    "2026",
}

FOLLOW_UP_PATTERNS = (
    r"\bit\b",
    r"\bthat\b",
    r"\bthis\b",
    r"\bthey\b",
    r"\bthem\b",
    r"\bthose\b",
)

CLARIFICATION_PATTERNS = (
    r"\bi\s+meant\b",
    r"\bi\s+mean\b",
    r"\bwhat\s+i\s+meant\b",
    r"\bactually\b",
    r"\binstead\b",
    r"\bnot\s+that\b",
    r"\bnot\s+the\b",
    r"\bto\s+clarify\b",
)


def _compact_prompt(prompt: str, *, limit: int = 180) -> str:
    compacted = re.sub(r"\s+", " ", prompt).strip()
    if len(compacted) <= limit:
        return compacted
    return compacted[:limit].rsplit(" ", 1)[0].strip()


def _meaningful_word_count(prompt: str) -> int:
    return len(re.findall(r"[A-Za-z0-9+#.-]{3,}", prompt))


def _looks_like_follow_up(prompt: str) -> bool:
    lowered = prompt.lower()
    if any(re.search(pattern, lowered) for pattern in CLARIFICATION_PATTERNS):
        return True
    if _meaningful_word_count(prompt) <= 2:
        return True
    return len(prompt.split()) <= 6 and any(re.search(pattern, lowered) for pattern in FOLLOW_UP_PATTERNS)


def _recent_context_for_follow_up(
    conversation_summary: str,
    recent_messages: list[dict[str, str]] | None,
) -> str:
    messages = recent_messages or []
    recent_user_bits = [
        message.get("content", "")
        for message in messages[-5:]
        if message.get("role") == "user" and message.get("content", "").strip()
    ]
    recent_assistant_bits = [
        message.get("content", "")
        for message in messages[-3:]
        if message.get("role") == "assistant" and message.get("content", "").strip()
    ]
    context_parts = [conversation_summary, *recent_user_bits[-2:]]
    if not recent_user_bits:
        context_parts.extend(recent_assistant_bits[-1:])
    return _compact_prompt(" ".join(context_parts), limit=140)


def build_search_query(
    prompt: str,
    *,
    conversation_summary: str = "",
    recent_messages: list[dict[str, str]] | None = None,
    max_terms: int = 10,
) -> str:
    _ = max_terms
    query = _compact_prompt(prompt)
    if _looks_like_follow_up(query):
        context = _recent_context_for_follow_up(conversation_summary, recent_messages)
        if context:
            query = _compact_prompt(f"{query} {context}")

    if not query:
        return _compact_prompt(prompt, limit=120)

    has_freshness = any(term in query.lower() for term in FRESHNESS_TERMS)
    if has_freshness and "latest" not in query.lower() and "recent" not in query.lower():
        query = _compact_prompt(f"{query} latest")
    return query
