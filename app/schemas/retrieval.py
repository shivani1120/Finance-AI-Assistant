from pydantic import BaseModel, Field, field_validator

from app.schemas.documents import DocumentType


class RetrievalFilters(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    reporting_year: int | None = Field(default=None, ge=1900, le=2100)
    document_type: DocumentType | None = None
    document_id: str | None = Field(default=None, min_length=1, max_length=64)

    def to_chroma_where(self) -> dict[str, object] | None:
        filters = self.model_dump(exclude_none=True)
        for key, value in filters.items():
            if isinstance(value, DocumentType):
                filters[key] = value.value
        if not filters:
            return None
        if len(filters) == 1:
            return filters
        return {"$and": [{key: value} for key, value in filters.items()]}


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    top_k: int | None = Field(default=None, ge=1)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be blank")
        return normalized


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    company: str
    reporting_year: int | None = None
    document_type: str
    page_number: int | None = None
    content: str
    distance: float = Field(description="Chroma cosine distance; smaller values rank closer")
    similarity_score: float = Field(
        description="Derived as 1 - cosine distance; a ranking score, not a probability"
    )


class RetrievalResponse(BaseModel):
    question: str
    result_count: int
    results: list[RetrievedChunk]
