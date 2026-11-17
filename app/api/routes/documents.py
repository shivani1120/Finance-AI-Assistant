import logging
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import get_settings
from app.rag.ingestion.embeddings import EmbeddingConfigurationError
from app.rag.ingestion.pdf_processor import PDFProcessingError
from app.schemas.documents import (
    DocumentType,
    DocumentUploadResponse,
    DocumentUrlImportRequest,
)
from app.services.document_ingestion import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


def _ingest_content(
    content: bytes,
    *,
    filename: str,
    company: str,
    reporting_year: int | None,
    document_type: DocumentType,
    current_user: User,
) -> DocumentUploadResponse:
    settings = get_settings()
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The file contents are not a PDF")
    normalized_company = company.strip()
    if not normalized_company:
        raise HTTPException(status_code=422, detail="Company must not be blank")

    try:
        return ingest_pdf(
            content,
            filename=filename,
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
        logger.exception("Document ingestion failed for filename=%s", filename)
        raise HTTPException(status_code=502, detail="Document processing failed") from exc


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
    return _ingest_content(
        content,
        filename=original_name,
        company=company,
        reporting_year=reporting_year,
        document_type=document_type,
        current_user=current_user,
    )


def _validate_report_url(url: str) -> None:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or host != "www.ril.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise HTTPException(
            status_code=422,
            detail="For now, use a public HTTPS PDF link from www.ril.com",
        )


@router.post("/import-url", response_model=DocumentUploadResponse, status_code=201)
def import_document_from_url(
    request: DocumentUrlImportRequest,
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    settings = get_settings()
    current_url = str(request.url)
    _validate_report_url(current_url)
    timeout = httpx.Timeout(30.0, connect=5.0)

    try:
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            for _ in range(4):
                with client.stream("GET", current_url, headers={"User-Agent": "FinanceAIReportImporter/1.0"}) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise HTTPException(status_code=502, detail="The report link returned an invalid redirect")
                        current_url = urljoin(current_url, location)
                        _validate_report_url(current_url)
                        continue
                    if response.status_code != 200:
                        raise HTTPException(status_code=502, detail="The report link could not be downloaded")

                    content = bytearray()
                    for chunk in response.iter_bytes(64 * 1024):
                        content.extend(chunk)
                        if len(content) > settings.max_upload_size_bytes:
                            raise HTTPException(
                                status_code=413,
                                detail=f"PDF exceeds the {settings.max_upload_size_mb} MB upload limit",
                            )
                    break
            else:
                raise HTTPException(status_code=502, detail="The report link redirected too many times")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.warning("Could not download report from configured public report host: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Could not download the PDF from that link") from exc

    if not bytes(content).startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The link did not return a PDF file")

    filename = Path(unquote(urlsplit(current_url).path)).name or "financial-report.pdf"
    if not filename.lower().endswith(".pdf"):
        filename = "financial-report.pdf"
    year_match = re.search(r"(20\d{2})[-_](\d{2})", filename)
    inferred_year = int(f"20{year_match.group(2)}") if year_match else None
    return _ingest_content(
        bytes(content),
        filename=filename,
        company=request.company or "Reliance Industries Limited",
        reporting_year=request.reporting_year or inferred_year,
        document_type=request.document_type,
        current_user=current_user,
    )
