from __future__ import annotations

import asyncio

from ...agents.streaming import chunk_text, sse_event


def friendly_agent_error(exc: Exception) -> str:
    message = str(exc).strip()
    lower = message.lower()
    exc_name = exc.__class__.__name__
    if (
        "connection reset" in lower
        or "forcibly closed" in lower
        or "connection aborted" in lower
        or exc_name in {"ConnectionError", "ChunkedEncodingError"}
    ):
        return (
            "A remote service closed the connection while Draftly was working. "
            "Retry once; if it happens again, the source or provider may be blocking the request."
        )
    if isinstance(exc, asyncio.TimeoutError) or "timeout" in lower or "timed out" in lower:
        return (
            "The request timed out before the answer finished. Try Quick mode, use a narrower question, "
            "or retry in a moment."
        )
    if "tavily" in lower:
        return (
            "Tavily search failed or timed out. Check your Tavily API key/network connection, "
            "or retry with a narrower topic."
        )
    if "gemini" in lower or "google" in lower or exc_name in {"ResourceExhausted", "GoogleAPIError", "InvalidArgument"}:
        return (
            "Gemini could not complete the request. Check the model name, API key, quota, and rate limits, "
            "then try again."
        )
    if "ollama" in lower:
        return "Ollama could not complete the request. Check that Ollama is running and the selected model is installed."
    return message or "Something went wrong while processing this topic. Please try again."


def format_usage_log(usage: dict | None, *, response_text: str, elapsed_seconds: float) -> str:
    if usage:
        input_tokens = usage.get("input_tokens") or usage.get("prompt_token_count") or usage.get("prompt_tokens")
        output_tokens = (
            usage.get("output_tokens")
            or usage.get("completion_token_count")
            or usage.get("completion_tokens")
        )
        total_tokens = usage.get("total_tokens") or usage.get("total_token_count")
        parts = []
        if input_tokens is not None:
            parts.append(f"input={input_tokens}")
        if output_tokens is not None:
            parts.append(f"output={output_tokens}")
        if total_tokens is not None:
            parts.append(f"total={total_tokens}")
        if parts:
            return f"Gemini usage: {', '.join(parts)}; elapsed={elapsed_seconds:.1f}s"
    estimated_output_tokens = max(1, round(len(response_text.split()) / 0.75)) if response_text else 0
    return f"Usage estimate: output~{estimated_output_tokens} tokens; elapsed={elapsed_seconds:.1f}s"


def stream_text_event(event_name: str, topic_id: str, text: str) -> list[str]:
    return [sse_event(event_name, {"topicId": topic_id, "text": piece}) for piece in chunk_text(text, 28)]
