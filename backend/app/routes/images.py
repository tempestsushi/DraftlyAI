from fastapi import APIRouter, HTTPException

from ..models import ImageGenerateRequest
from ..services.images import generate_images
from ..store import store

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/generate")
async def generate_image_options(payload: ImageGenerateRequest) -> list[dict]:
    draft = None
    if payload.draft_id:
        draft = store.get_draft(payload.draft_id)
        if draft is None:
            raise HTTPException(status_code=404, detail="Draft not found")

    try:
        results = generate_images(payload.prompt, use_case=payload.use_case, count=payload.count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc
    if draft:
        for result in results:
            store.save_draft_image(
                draft_id=draft.id,
                topic_id=draft.topic_id,
                title=result.title,
                image_url=result.image_url,
                thumbnail_url=result.thumbnail_url,
                source_url=result.source_url,
                source_domain=result.source_domain,
                provider=result.provider,
                width=result.width,
                height=result.height,
            )
    return [result.model_dump(mode="json") for result in results]
