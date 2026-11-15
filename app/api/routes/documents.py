import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import get_settings
from app.rag.ingestion.embeddings import EmbeddingConfigurationError
from app.rag.ingestion.pdf_processor import PDFProcessingError
from app.schemas.documents import DocumentType, DocumentUploadResponse
from app.services.document_ingestion import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
def upload_document(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    company: str = Form(..., min_length=1, max_length=200),
    reporting_year: int | None = Form(default=None, ge=1900, le=2100),
    document_type: DocumentType = Form(...),
) -> DocumentUploadResponse:
    settings = get_settings()
    original_name = Path(file.filename or "").name
    if not original_name or Path(original_name).suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only .pdf files are supported")
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="The uploaded file must be a PDF")

    content = file.file.read(settings.max_upload_size_bytes + 1)
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"PDF exceeds the {settings.max_upload_size_mb} MB upload limit",
        )
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The file contents are not a PDF")

    normalized_company = company.strip()
    if not normalized_company:
        raise HTTPException(status_code=422, detail="Company must not be blank")

    try:
        return ingest_pdf(
            content,
            filename=original_name,
            company=normalized_company,
            reporting_year=reporting_year,
            document_type=document_type,
            user_id=str(current_user.id),
            settings=settings,
        )
    except PDFProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document ingestion failed for filename=%s", original_name)
        raise HTTPException(status_code=502, detail="Document processing failed") from exc
