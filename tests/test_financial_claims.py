from app.guardrails.output.financial_claims import financial_claim_error
from app.schemas.chat import ChatSource
from app.schemas.retrieval import RetrievedChunk


def _source_data() -> tuple[list[ChatSource], list[RetrievedChunk]]:
    source = ChatSource(
        source_id="S1",
        document_id="report-1",
        filename="annual-report.pdf",
        page_number=12,
        chunk_id="chunk-1",
    )
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        document_id="report-1",
        filename="annual-report.pdf",
        company="Example Industries",
        reporting_year=2025,
        document_type="annual_report",
        page_number=12,
        content="Revenue was INR 1,000 crore and operating profit was INR 150 crore.",
        distance=0.1,
        similarity_score=0.9,
    )
    return [source], [chunk]


def test_paragraph_end_citation_supports_its_financial_sentences() -> None:
    sources, chunks = _source_data()
    answer = (
        "Revenue was INR 1,000 crore. Operating profit was INR 150 crore. [S1]"
    )

    assert financial_claim_error(answer, sources, chunks) is None


def test_paragraph_citation_does_not_allow_unsupported_numbers() -> None:
    sources, chunks = _source_data()
    answer = "Revenue was INR 1,200 crore. [S1]"

    assert financial_claim_error(answer, sources, chunks) == "unsupported_numeric_claim"


def test_financial_claim_still_requires_a_citation() -> None:
    sources, chunks = _source_data()
    answer = "Revenue was INR 1,000 crore."

    assert financial_claim_error(answer, sources, chunks) == "uncited_financial_claim"
