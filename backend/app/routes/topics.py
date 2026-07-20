from fastapi import APIRouter, HTTPException

from ..models import MessageRole, MessageUpdateRequest, TopicDraftRequest
from ..services.agent import create_draft_from_topic_response
from ..store import store

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
async def list_topics() -> list[dict]:
    return [topic.model_dump(mode="json") for topic in store.list_topics()]


@router.get("/{topic_id}")
async def get_topic(topic_id: str) -> dict:
    topic = store.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic.model_dump(mode="json")


@router.get("/{topic_id}/messages")
async def list_topic_messages(topic_id: str) -> list[dict]:
    topic = store.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return [message.model_dump(mode="json") for message in store.list_messages(topic_id)]


@router.patch("/{topic_id}/messages/{message_id}")
async def update_topic_message(topic_id: str, message_id: str, payload: MessageUpdateRequest) -> dict:
    topic = store.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    existing = next((message for message in store.list_messages(topic_id) if message.id == message_id), None)
    if existing is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if existing.role != MessageRole.user:
        raise HTTPException(status_code=400, detail="Only user prompts can be edited")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Prompt content is required")

    updated = store.update_message(topic_id, message_id, content)
    if updated is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return updated.model_dump(mode="json")


@router.get("/{topic_id}/sources")
async def list_topic_sources(topic_id: str) -> list[dict]:
    topic = store.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return [source.model_dump(mode="json") for source in store.list_message_sources(topic_id)]


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str) -> dict:
    deleted = store.delete_topic(topic_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"ok": True}


@router.post("/{topic_id}/draft")
async def create_topic_draft(topic_id: str, payload: TopicDraftRequest | None = None) -> dict:
    try:
        draft = await create_draft_from_topic_response(
            store,
            topic_id,
            payload.title if payload else None,
            payload.message_id if payload else None,
            tone=payload.tone if payload else TopicDraftRequest.model_fields["tone"].default,
            length=payload.length if payload else TopicDraftRequest.model_fields["length"].default,
            include_cta=payload.include_cta if payload else True,
            include_hashtags=payload.include_hashtags if payload else True,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Draft generation timed out") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return draft.model_dump(mode="json")
