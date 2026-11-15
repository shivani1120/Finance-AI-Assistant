from app.guardrails.output.citations import validate_citation_ids
from app.guardrails.output.financial_claims import financial_claim_error
from app.guardrails.output.investment_advice import contains_personalized_recommendation
from app.guardrails.types import OutputDecision
from app.schemas.chat import ChatSource
from app.schemas.retrieval import RetrievedChunk


def validate_answer(
    answer: str,
    sources: list[ChatSource],
    chunks: list[RetrievedChunk],
) -> OutputDecision:
    if not answer.strip():
        return OutputDecision(False, "invalid_output")
    if contains_personalized_recommendation(answer):
        return OutputDecision(False, "personalized_advice_output")
    if not validate_citation_ids(answer, sources):
        return OutputDecision(False, "invalid_citation")
    claim_error = financial_claim_error(answer, sources, chunks)
    if claim_error is not None:
        return OutputDecision(False, claim_error)
    return OutputDecision(True, "valid")
