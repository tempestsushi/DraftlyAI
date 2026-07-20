from fastapi import APIRouter, HTTPException

from ..models import DraftImageSaveRequest, DraftRegenerateRequest, DraftUpdateRequest
from ..services.agent import regenerate_draft_from_same_answer
from ..store import store

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("")
async def list_drafts(topic_id: str | None = None) -> list[dict]:
    drafts = store.list_drafts()
    if topic_id is not None:
        drafts = [draft for draft in drafts if draft.topic_id == topic_id]
    return [draft.model_dump(mode="json") for draft in drafts]


@router.get("/{draft_id}")
async def get_draft(draft_id: str) -> dict:
    draft = store.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft.model_dump(mode="json")


@router.patch("/{draft_id}")
async def update_draft(draft_id: str, payload: DraftUpdateRequest) -> dict:
    draft = store.update_draft(
        draft_id,
        content=payload.content,
        status=payload.status,
        clear_linkedin_post=payload.clear_linkedin_post,
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft.model_dump(mode="json")


@router.get("/{draft_id}/versions")
async def list_draft_versions(draft_id: str) -> list[dict]:
    if store.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return [version.model_dump(mode="json") for version in store.list_draft_versions(draft_id)]


@router.get("/{draft_id}/image")
async def get_draft_image(draft_id: str) -> dict | None:
    if store.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    image = store.get_draft_image(draft_id)
    return image.model_dump(mode="json") if image else None


@router.get("/{draft_id}/images")
async def list_draft_images(draft_id: str) -> list[dict]:
    if store.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return [image.model_dump(mode="json") for image in store.list_draft_images(draft_id)]


@router.post("/{draft_id}/image")
async def save_draft_image(draft_id: str, payload: DraftImageSaveRequest) -> dict:
    draft = store.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    image = store.save_draft_image(
        draft_id=draft_id,
        topic_id=draft.topic_id,
        title=payload.title,
        image_url=payload.image_url,
        thumbnail_url=payload.thumbnail_url,
        source_url=payload.source_url,
        source_domain=payload.source_domain,
        provider=payload.provider,
        width=payload.width,
        height=payload.height,
    )
    return image.model_dump(mode="json")


@router.post("/{draft_id}/images")
async def add_draft_image(draft_id: str, payload: DraftImageSaveRequest) -> dict:
    return await save_draft_image(draft_id, payload)


@router.delete("/{draft_id}/image")
async def delete_draft_image(draft_id: str) -> dict:
    if store.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    deleted = store.delete_draft_image(draft_id)
    return {"deleted": deleted}


@router.delete("/{draft_id}/images/{image_id}")
async def delete_one_draft_image(draft_id: str, image_id: str) -> dict:
    if store.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    deleted = store.delete_draft_image_by_id(draft_id, image_id)
    return {"deleted": deleted}


@router.post("/{draft_id}/regenerate")
async def regenerate_draft(draft_id: str, payload: DraftRegenerateRequest) -> dict:
    try:
        draft = await regenerate_draft_from_same_answer(
            store,
            draft_id,
            tone=payload.tone,
            length=payload.length,
            include_cta=payload.include_cta,
            include_hashtags=payload.include_hashtags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return draft.model_dump(mode="json")
