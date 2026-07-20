from fastapi import APIRouter

from ..models import RagEvaluationRequest
from ..services.rag_evaluation import run_rag_evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/rag")
def run_rag_comparison(payload: RagEvaluationRequest) -> dict[str, object]:
    return run_rag_evaluation(
        payload.prompt,
        payload.research_depth,
        include_responses=payload.include_responses,
    )
