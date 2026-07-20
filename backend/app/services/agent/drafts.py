from __future__ import annotations

import asyncio
import sys

from ...config import settings
from ...models import DraftLength, DraftRecord, DraftStatus, DraftTone, LogSource, MessageRole, TopicStatus
from ...store import Store


def _create_agent_graph(**kwargs):
    return sys.modules[__package__].create_agent_graph(**kwargs)


async def create_draft_from_topic_response(
    store: Store,
    topic_id: str,
    title: str | None = None,
    message_id: str | None = None,
    *,
    tone: DraftTone = DraftTone.professional,
    length: DraftLength = DraftLength.medium,
    include_cta: bool = True,
    include_hashtags: bool = True,
) -> DraftRecord:
    topic = store.get_topic(topic_id)
    if topic is None:
        raise ValueError("Topic not found")
    messages = store.list_messages(topic_id)
    assistant_messages = [message for message in messages if message.role == MessageRole.assistant]
    target_message = None
    if message_id is not None:
        target_message = next((message for message in assistant_messages if message.id == message_id), None)
        if target_message is None:
            raise ValueError("The selected assistant message was not found in this chat")
    elif assistant_messages:
        target_message = assistant_messages[-1]

    response_content = target_message.content if target_message is not None else topic.response_content
    if not response_content:
        raise ValueError("No saved answer is available for this topic yet")

    existing_drafts = [
        draft
        for draft in store.list_drafts()
        if draft.topic_id == topic_id and draft.source_message_id == (target_message.id if target_message else None)
    ]
    if existing_drafts:
        return existing_drafts[0]

    store.update_topic_status(topic_id, TopicStatus.drafting)
    store.add_log(topic_id, LogSource.ollama, "Creating LinkedIn draft from saved chat answer")
    agent = _create_agent_graph(max_output_tokens=settings.gemini_draft_output_tokens)
    try:
        draft_content = await agent.build_draft_from_answer_with_options(
            topic.topic,
            response_content,
            tone=tone,
            length=length,
            include_cta=include_cta,
            include_hashtags=include_hashtags,
        )
    except asyncio.TimeoutError as exc:
        store.update_topic_status(topic_id, TopicStatus.complete)
        store.add_log(topic_id, LogSource.system, "Draft generation timed out before completion")
        raise ValueError(
            "Draft generation timed out. Please try again, or use a shorter answer / lighter draft settings."
        ) from exc
    if getattr(agent, "last_draft_repair_performed", False):
        store.add_log(topic_id, LogSource.system, "Draft looked incomplete, so it was completed before saving")

    draft = store.add_draft(
        title=title or target_message.content[:80] or topic.topic,
        content=draft_content,
        source="research",
        topic_id=topic_id,
        source_message_id=target_message.id if target_message else None,
    )
    store.update_topic_status(topic_id, TopicStatus.review)
    store.add_log(topic_id, LogSource.system, "LinkedIn draft created from chat answer")
    return draft


async def regenerate_draft_from_same_answer(
    store: Store,
    draft_id: str,
    *,
    tone: DraftTone = DraftTone.professional,
    length: DraftLength = DraftLength.medium,
    include_cta: bool = True,
    include_hashtags: bool = True,
) -> DraftRecord:
    draft = store.get_draft(draft_id)
    if draft is None:
        raise ValueError("Draft not found")
    if draft.topic_id is None:
        raise ValueError("This draft is not linked to a chat answer")

    topic = store.get_topic(draft.topic_id)
    if topic is None:
        raise ValueError("Draft topic not found")

    messages = store.list_messages(draft.topic_id)
    source_message = next((message for message in messages if message.id == draft.source_message_id), None)
    latest_assistant_message = next(
        (message for message in reversed(messages) if message.role == MessageRole.assistant),
        None,
    )
    response_content = (
        source_message.content
        if source_message is not None
        else topic.response_content or (latest_assistant_message.content if latest_assistant_message else None)
    )
    if not response_content:
        raise ValueError("No saved answer is available for this draft")

    store.update_topic_status(draft.topic_id, TopicStatus.drafting)
    store.add_log(draft.topic_id, LogSource.ollama, "Regenerating LinkedIn draft from the same chat answer")
    agent = _create_agent_graph(max_output_tokens=settings.gemini_draft_output_tokens)
    try:
        draft_content = await agent.build_draft_from_answer_with_options(
            topic.topic,
            response_content,
            tone=tone,
            length=length,
            include_cta=include_cta,
            include_hashtags=include_hashtags,
        )
    except asyncio.TimeoutError as exc:
        store.update_topic_status(draft.topic_id, TopicStatus.review)
        store.add_log(draft.topic_id, LogSource.system, "Draft regeneration timed out before completion")
        raise ValueError(
            "Draft regeneration timed out. Try a shorter length or regenerate again."
        ) from exc
    if getattr(agent, "last_draft_repair_performed", False):
        store.add_log(draft.topic_id, LogSource.system, "Regenerated draft looked incomplete, so it was completed before saving")

    updated = store.update_draft(
        draft.id,
        content=draft_content,
        status=DraftStatus.pending,
        version_reason="regenerated",
    )
    if updated is None:
        raise ValueError("Draft not found")
    store.update_topic_status(draft.topic_id, TopicStatus.review)
    store.add_log(draft.topic_id, LogSource.system, "LinkedIn draft regenerated from the saved chat answer")
    return updated
