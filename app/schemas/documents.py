from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class DocumentType(StrEnum):
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    EARNINGS_REPORT = "earnings_report"
    FINANCIAL_STATEMENT = "financial_statement"
    INVESTOR_PRESENTATION = "investor_presentation"
    OTHER = "other"


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    company: str
    reporting_year: int | None
    document_type: DocumentType
    chunk_count: int = Field(ge=1)
    status: str = "processed"


class DocumentUrlImportRequest(BaseModel):
    url: HttpUrl
    company: str | None = Field(default=None, min_length=1, max_length=200)
    reporting_year: int | None = Field(default=None, ge=1900, le=2100)
    document_type: DocumentType = DocumentType.ANNUAL_REPORT
