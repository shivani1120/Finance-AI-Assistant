import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.auth.dependencies import DbSession
from app.auth.models import User
from app.core.config import get_settings
from app.rag.generation.answer_generator import AnswerGenerationError
from app.rag.generation.llm_factory import LLMConfigurationError
from app.rag.ingestion.embeddings import EmbeddingConfigurationError
from app.rag.retrieval.retriever import RetrievalServiceError
from app.schemas.chat import ChatRequest, ChatResponse
from app.history.service import QueryHistoryPersistenceError, record_chat_exchange
from app.guardrails.input.validator import validate_question
from app.services.chat_service import answer_question

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    settings = get_settings()
    top_k = request.top_k or settings.retrieval_top_k
    if top_k > settings.retrieval_max_top_k:
        raise HTTPException(
            status_code=422,
            detail=f"top_k cannot exceed {settings.retrieval_max_top_k}",
        )

    try:
        response = answer_question(request, settings, user_id=str(current_user.id))
        if validate_question(request.question).allowed:
            record_chat_exchange(db, user_id=current_user.id, request=request, response=response)
        return response
    except (EmbeddingConfigurationError, LLMConfigurationError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (RetrievalServiceError, AnswerGenerationError) as exc:
        logger.warning("RAG dependency failed: %s", exc)
        raise HTTPException(status_code=503, detail="RAG service is unavailable") from exc
    except QueryHistoryPersistenceError as exc:
        logger.exception("Chat history could not be persisted for user_id=%s", current_user.id)
        raise HTTPException(status_code=503, detail="Chat history could not be saved") from exc
