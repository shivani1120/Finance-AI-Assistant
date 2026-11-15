from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.history.models import QueryHistory
from app.schemas.chat import ChatRequest, ChatResponse


class QueryHistoryPersistenceError(RuntimeError):
    """Raised when a completed chat exchange cannot be saved."""


def record_chat_exchange(
    db: Session,
    *,
    user_id: int,
    request: ChatRequest,
    response: ChatResponse,
) -> QueryHistory:
    entry = QueryHistory(
        user_id=user_id,
        question=request.question,
        answer=response.answer,
        sources=[source.model_dump(mode="json") for source in response.sources],
    )
    db.add(entry)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise QueryHistoryPersistenceError("Chat history could not be saved") from exc
    db.refresh(entry)
    return entry


def list_user_history(
    db: Session,
    *,
    user_id: int,
    limit: int,
    offset: int,
) -> tuple[list[QueryHistory], int]:
    entries = list(
        db.scalars(
            select(QueryHistory)
            .where(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc(), QueryHistory.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    total = db.scalar(
        select(func.count()).select_from(QueryHistory).where(QueryHistory.user_id == user_id)
    )
    return entries, int(total or 0)
