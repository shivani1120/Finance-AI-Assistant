import re
from decimal import Decimal, InvalidOperation

from app.schemas.chat import ChatSource
from app.schemas.retrieval import RetrievedChunk

FINANCIAL_CLAIM_PATTERN = re.compile(
    r"\b(revenue|sales|income|earnings|profit|loss|margin|cash\s+flow|balance\s+sheet|"
    r"asset|liabilit\w*|debt|dividend|equity|stock|share|market\s+cap|financial|"
    r"increased|decreased|grew|declined|rose|fell|percent|percentage|billion|million)\b",
    re.I,
)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(-?\d[\d,]*(?:\.\d+)?)\s*(%|percent)?(?![A-Za-z])",
    re.I,
)


def _normalized_numbers(text: str) -> set[tuple[Decimal, bool]]:
    numbers: set[tuple[Decimal, bool]] = set()
    for raw_value, percent_marker in NUMBER_PATTERN.findall(text):
        try:
            value = Decimal(raw_value.replace(",", ""))
        except InvalidOperation:
            continue
        numbers.add((value.normalize(), bool(percent_marker)))
    return numbers


def financial_claim_error(
    answer: str,
    sources: list[ChatSource],
    chunks: list[RetrievedChunk],
) -> str | None:
    """Require citations on finance/number claims and check their numbers occur in cited text."""
    source_by_id = {source.source_id.upper(): source for source in sources}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}

    for sentence in SENTENCE_PATTERN.split(answer):
        sentence = sentence.strip()
        if not sentence:
            continue
        numbers = _normalized_numbers(sentence)
        if not numbers and not FINANCIAL_CLAIM_PATTERN.search(sentence):
            continue

        cited_ids = {
            citation.upper()
            for citation in re.findall(r"\[(S\d+)\]", sentence, flags=re.IGNORECASE)
        }
        if not cited_ids:
            return "uncited_financial_claim"

        cited_text_parts: list[str] = []
        for source_id in cited_ids:
            source = source_by_id.get(source_id)
            if source is None:
                continue
            chunk = chunk_by_id.get(source.chunk_id)
            if chunk is not None:
                cited_text_parts.append(
                    f"{chunk.content} reporting year {chunk.reporting_year or ''} "
                    f"page {chunk.page_number or ''}"
                )
        source_numbers = _normalized_numbers(" ".join(cited_text_parts))
        if numbers - source_numbers:
            return "unsupported_numeric_claim"
    return None
