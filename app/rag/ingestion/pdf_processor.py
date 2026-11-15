from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.schemas.documents import DocumentType


class PDFProcessingError(ValueError):
    """Raised when a PDF cannot produce usable text chunks."""


def load_and_chunk_pdf(
    pdf_path: Path,
    *,
    document_id: str,
    filename: str,
    company: str,
    reporting_year: int | None,
    document_type: DocumentType,
    user_id: str,
    settings: Settings,
) -> list[Document]:
    """Extract page text, clean it, split it, and attach searchable metadata."""
    try:
        pages = PyMuPDFLoader(str(pdf_path)).load()
    except Exception as exc:
        raise PDFProcessingError("The PDF could not be read") from exc

    usable_pages: list[Document] = []
    for page in pages:
        cleaned_lines = [
            " ".join(line.split())
            for line in page.page_content.splitlines()
            if line.strip()
        ]
        cleaned_text = "\n".join(cleaned_lines)
        if not cleaned_text:
            continue
        page_number = int(page.metadata.get("page", 0)) + 1
        usable_pages.append(
            Document(
                page_content=cleaned_text,
                metadata={"page_number": page_number},
            )
        )

    if not usable_pages:
        raise PDFProcessingError(
            "No selectable text was found. Scanned PDFs need OCR, which is not included yet."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(usable_pages)

    for index, chunk in enumerate(chunks):
        chunk_id = f"{document_id}:{index}"
        chunk.metadata.update(
            {
                "document_id": document_id,
                "filename": filename,
                "company": company,
                "document_type": document_type.value,
                "chunk_id": chunk_id,
                "chunk_index": index,
                "user_id": user_id,
            }
        )
        if reporting_year is not None:
            chunk.metadata["reporting_year"] = reporting_year
        chunk.id = chunk_id

    return chunks
