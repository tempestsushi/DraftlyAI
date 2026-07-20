from fastapi import APIRouter

from ..config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    model = settings.gemini_model if settings.model_provider == "gemini" else settings.ollama_model
    return {
        "ok": True,
        "service": settings.app_name,
        "model_provider": settings.model_provider,
        "model": model,
    }
