from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import ChatSource


class QueryHistoryRead(BaseModel):
    id: int
    question: str
    answer: str
    sources: list[ChatSource]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryHistoryPage(BaseModel):
    items: list[QueryHistoryRead]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
