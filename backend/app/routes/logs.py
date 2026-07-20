from fastapi import APIRouter

from ..store import store

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def list_logs(topic_id: str | None = None) -> list[dict]:
    return [log.model_dump(mode="json") for log in store.list_logs(topic_id)]
