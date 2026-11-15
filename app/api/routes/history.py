from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, select

from app.auth.dependencies import CurrentUser, DbSession
from app.history.models import QueryHistory
from app.history.schemas import QueryHistoryPage, QueryHistoryRead
from app.history.service import list_user_history

router = APIRouter(prefix="/history", tags=["query history"])


@router.get("", response_model=QueryHistoryPage)
def get_history(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> QueryHistoryPage:
    entries, total = list_user_history(db, user_id=user.id, limit=limit, offset=offset)
    return QueryHistoryPage(items=entries, limit=limit, offset=offset, total=total)


@router.get("/{entry_id}", response_model=QueryHistoryRead)
def get_history_entry(entry_id: int, user: CurrentUser, db: DbSession) -> QueryHistory:
    entry = db.scalar(
        select(QueryHistory).where(
            QueryHistory.id == entry_id,
            QueryHistory.user_id == user.id,
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    return entry


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_history(user: CurrentUser, db: DbSession) -> Response:
    db.execute(delete(QueryHistory).where(QueryHistory.user_id == user.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_entry(entry_id: int, user: CurrentUser, db: DbSession) -> Response:
    entry = db.scalar(
        select(QueryHistory).where(
            QueryHistory.id == entry_id,
            QueryHistory.user_id == user.id,
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
