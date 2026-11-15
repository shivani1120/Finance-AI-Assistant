from enum import StrEnum

from pydantic import BaseModel, Field


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
