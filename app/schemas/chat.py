from pydantic import BaseModel

from app.schemas.retrieval import RetrievalRequest


class ChatRequest(RetrievalRequest):
    """Question plus the same optional retrieval controls used by search."""


class ChatSource(BaseModel):
    source_id: str
    document_id: str
    filename: str
    page_number: int | None = None
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
