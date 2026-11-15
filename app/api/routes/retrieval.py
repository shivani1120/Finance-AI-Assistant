import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import get_settings
from app.rag.ingestion.embeddings import EmbeddingConfigurationError
from app.rag.retrieval.retriever import RetrievalServiceError, retrieve_chunks
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
def search_documents(
    request: RetrievalRequest,
    current_user: User = Depends(get_current_user),
) -> RetrievalResponse:
    settings = get_settings()
    top_k = request.top_k or settings.retrieval_top_k
    if top_k > settings.retrieval_max_top_k:
        raise HTTPException(
            status_code=422,
            detail=f"top_k cannot exceed {settings.retrieval_max_top_k}",
        )

    try:
        results = retrieve_chunks(
            request.question,
            filters=request.filters,
            user_id=str(current_user.id),
            top_k=top_k,
            settings=settings,
        )
    except EmbeddingConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RetrievalServiceError as exc:
        logger.warning("Retrieval dependency failed: %s", exc)
        raise HTTPException(status_code=503, detail="Retrieval service is unavailable") from exc

    return RetrievalResponse(
        question=request.question,
        result_count=len(results),
        results=results,
    )
