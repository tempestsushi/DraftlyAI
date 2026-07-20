from __future__ import annotations

from ...models import MessageRole
from ...store import Store


def resolve_regeneration_prompt(
    store: Store,
    topic_id: str | None,
    regenerate_message_id: str | None,
    fallback_topic: str,
) -> tuple[str, bool]:
    if not regenerate_message_id:
        return fallback_topic, False
    if not topic_id:
        raise ValueError("A chat id is required to regenerate an answer")
    messages = store.list_messages(topic_id)
    target_index = next((index for index, message in enumerate(messages) if message.id == regenerate_message_id), None)
    if target_index is None or messages[target_index].role != MessageRole.assistant:
        raise ValueError("The selected assistant message was not found in this chat")
    for message in reversed(messages[:target_index]):
        if message.role == MessageRole.user:
            return message.content, True
    raise ValueError("Could not find the user prompt for this answer")


def sanitize_response_style(response_style: str | None) -> str:
    if not response_style:
        return ""
    return " ".join(response_style.split())[:300]
