from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.rag.ingestion.pdf_processor import load_and_chunk_pdf
from app.rag.ingestion.vector_store import store_chunks
from app.schemas.documents import DocumentType, DocumentUploadResponse


def ingest_pdf(
    content: bytes,
    *,
    filename: str,
    company: str,
    reporting_year: int | None,
    document_type: DocumentType,
    user_id: str,
    settings: Settings,
) -> DocumentUploadResponse:
    document_id = str(uuid4())
    document_directory = settings.upload_dir / document_id
    stored_pdf = document_directory / filename
    document_directory.mkdir(parents=True, exist_ok=False)

    try:
        stored_pdf.write_bytes(content)
        chunks = load_and_chunk_pdf(
            stored_pdf,
            document_id=document_id,
            filename=filename,
            company=company,
            reporting_year=reporting_year,
            document_type=document_type,
            user_id=user_id,
            settings=settings,
        )
        store_chunks(chunks, settings)
    except Exception:
        stored_pdf.unlink(missing_ok=True)
        document_directory.rmdir()
        raise

    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        company=company,
        reporting_year=reporting_year,
        document_type=document_type,
        chunk_count=len(chunks),
    )
