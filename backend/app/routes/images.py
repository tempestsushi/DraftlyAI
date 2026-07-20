from fastapi import APIRouter, HTTPException

from ..models import ImageGenerateRequest
from ..services.images import generate_images

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/generate")
async def generate_image_options(payload: ImageGenerateRequest) -> list[dict]:
    try:
        results = generate_images(payload.prompt, use_case=payload.use_case, count=payload.count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc
    return [result.model_dump(mode="json") for result in results]
