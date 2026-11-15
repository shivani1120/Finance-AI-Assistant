from typing import Literal

from typing_extensions import TypedDict

from app.schemas.chat import ChatSource
from app.schemas.retrieval import RetrievalFilters, RetrievedChunk


class RAGState(TypedDict, total=False):
    question: str
    search_query: str
    user_id: str | None
    filters: RetrievalFilters
    top_k: int
    intent: Literal["financial_fact", "causal_explanation", "comparison", "risk_summary"]
    retrieved_chunks: list[RetrievedChunk]
    context: str
    answer: str
    sources: list[ChatSource]
    guardrail_message: str
    unsafe_document_chunk_count: int
    validation_result: Literal[
        "valid",
        "invalid_input",
        "prompt_injection",
        "sensitive_personal_data",
        "personalized_investment_advice",
        "out_of_scope",
        "no_evidence",
        "invalid_output",
        "invalid_citation",
        "uncited_financial_claim",
        "unsupported_numeric_claim",
        "personalized_advice_output",
    ]
