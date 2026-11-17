import re
from typing import Literal

from app.core.config import Settings
from app.graph.state import RAGState
from app.rag.generation.answer_generator import generate_grounded_answer
from app.guardrails.documents.prompt_injection import remove_unsafe_chunks
from app.guardrails.input.validator import validate_question
from app.guardrails.output.validator import validate_answer
from app.rag.retrieval.retriever import retrieve_chunks
from app.schemas.chat import ChatSource
from app.schemas.retrieval import RetrievalFilters

NO_EVIDENCE_ANSWER = (
    "I could not find relevant information in the uploaded documents to answer that question."
)
SAFE_FALLBACK_ANSWER = (
    "I found related report passages, but could not safely verify the answer against them. "
    "Try asking about one figure, topic, or reporting year at a time."
)
VALIDATION_MESSAGES = {
    "invalid_citation": (
        "I found related passages, but the answer's citations did not match them. "
        "Try a narrower question about a specific report or year."
    ),
    "uncited_financial_claim": (
        "I found related passages, but could not attach a clear citation to every financial claim. "
        "Try asking about one figure or topic at a time."
    ),
    "unsupported_numeric_claim": (
        "I found related passages, but one or more numbers could not be verified in the cited text. "
        "Try asking for a specific figure and its report page."
    ),
    "invalid_output": "The answer could not be formatted safely. Please try again.",
}


def validate_input_node(state: RAGState) -> dict:
    question = state.get("question", "").strip()
    decision = validate_question(question)
    return {
        "question": question,
        "validation_result": decision.category,
        "guardrail_message": decision.message or "",
    }


def route_after_input_validation(
    state: RAGState,
) -> Literal["query_analysis", "safe_response"]:
    return "query_analysis" if state.get("validation_result") == "valid" else "safe_response"


def analyze_query_node(state: RAGState) -> dict:
    """Classify question intent to guide retrieval context and answer shape."""
    question = state["question"]
    normalized = question.lower()
    if re.search(r"\b(compare|comparison|versus|vs\.?|difference|changed|change)\b", normalized):
        intent = "comparison"
    elif re.search(r"\b(why|cause|caused|driver|drivers|increase because|decrease because)\b", normalized):
        intent = "causal_explanation"
    elif re.search(r"\b(risk|risks|uncertaint|challenge|threat)\w*\b", normalized):
        intent = "risk_summary"
    else:
        intent = "financial_fact"
    return {"search_query": question, "intent": intent}


def make_retrieval_node(settings: Settings):
    def retrieve_node(state: RAGState) -> dict:
        chunks = retrieve_chunks(
            state["search_query"],
            filters=state.get("filters", RetrievalFilters()),
            user_id=str(state["user_id"]),
            top_k=state["top_k"],
            settings=settings,
        )
        return {"retrieved_chunks": chunks}

    return retrieve_node


def route_after_retrieval(state: RAGState) -> Literal["document_safety", "no_evidence"]:
    return "document_safety" if state.get("retrieved_chunks") else "no_evidence"


def document_safety_node(state: RAGState) -> dict:
    safe_chunks, removed_count = remove_unsafe_chunks(state.get("retrieved_chunks", []))
    return {
        "retrieved_chunks": safe_chunks,
        "unsafe_document_chunk_count": removed_count,
    }


def route_after_document_safety(state: RAGState) -> Literal["context_construction", "no_evidence"]:
    return "context_construction" if state.get("retrieved_chunks") else "no_evidence"


def construct_context_node(state: RAGState) -> dict:
    context_parts: list[str] = []
    sources: list[ChatSource] = []
    for index, chunk in enumerate(state.get("retrieved_chunks", []), start=1):
        source_id = f"S{index}"
        context_parts.append(
            f"[{source_id}]\n"
            f"Document: {chunk.filename}; company: {chunk.company}; "
            f"reporting year: {chunk.reporting_year}; page: {chunk.page_number}; "
            f"chunk: {chunk.chunk_id}\n"
            f"Excerpt:\n{chunk.content}"
        )
        sources.append(
            ChatSource(
                source_id=source_id,
                document_id=chunk.document_id,
                filename=chunk.filename,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
            )
        )
    return {"context": "\n\n".join(context_parts), "sources": sources}


def make_generation_node(settings: Settings):
    def generate_node(state: RAGState) -> dict:
        answer = generate_grounded_answer(
            question=state["question"],
            intent=state.get("intent", "financial_fact"),
            context=state["context"],
            settings=settings,
        )
        return {"answer": answer}

    return generate_node


def validate_output_node(state: RAGState) -> dict:
    answer = state.get("answer", "").strip()
    decision = validate_answer(
        answer,
        state.get("sources", []),
        state.get("retrieved_chunks", []),
    )
    return {"answer": answer, "validation_result": decision.category}


def route_after_output_validation(state: RAGState) -> Literal["end", "safe_response"]:
    return "end" if state.get("validation_result") == "valid" else "safe_response"


def no_evidence_node(_: RAGState) -> dict:
    return {
        "answer": NO_EVIDENCE_ANSWER,
        "sources": [],
        "validation_result": "no_evidence",
    }


def safe_response_node(state: RAGState) -> dict:
    if state.get("guardrail_message"):
        answer = state["guardrail_message"]
    elif state.get("validation_result") == "personalized_advice_output":
        answer = (
            "I can't make personalized buy, sell, or hold recommendations. "
            "I can summarize factual information in the uploaded documents."
        )
    else:
        answer = VALIDATION_MESSAGES.get(
            state.get("validation_result", ""), SAFE_FALLBACK_ANSWER
        )
    preserved_sources = state.get("sources", []) if state.get("retrieved_chunks") else []
    return {"answer": answer, "sources": preserved_sources}
