from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ..models import ResearchDepth
from ..services.agent import stream_agent_run
from ..store import store

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/stream")
async def agent_stream(
    topic: str = Query(min_length=3, max_length=300),
    topic_id: str | None = Query(default=None),
    research_depth: ResearchDepth = Query(default=ResearchDepth.moderate),
    regenerate_message_id: str | None = Query(default=None),
    replace_user_message_id: str | None = Query(default=None),
    response_style: str | None = Query(default=None, max_length=300),
) -> StreamingResponse:
    async def event_generator():
        async for event in stream_agent_run(
            store,
            topic,
            topic_id=topic_id,
            research_depth=research_depth,
            regenerate_message_id=regenerate_message_id,
            replace_user_message_id=replace_user_message_id,
            response_style=response_style,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
