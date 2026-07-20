from fastapi import APIRouter, HTTPException

from ..models import IntegrationUpdateRequest
from ..store import store

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("")
async def list_integrations() -> list[dict]:
    return [integration.model_dump(mode="json") for integration in store.list_integrations()]


@router.patch("/{integration_id}")
async def update_integration(integration_id: str, payload: IntegrationUpdateRequest) -> dict:
    integration = store.update_integration(
        integration_id,
        status=payload.status,
        connected_at=payload.connected_at,
    )
    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration.model_dump(mode="json")
