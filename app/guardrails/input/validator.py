from app.guardrails.input.finance_scope import is_finance_document_question
from app.guardrails.input.investment_advice import requests_personalized_investment_advice
from app.guardrails.input.personal_data import requests_sensitive_personal_data
from app.guardrails.input.prompt_injection import is_prompt_injection_attempt
from app.guardrails.types import GuardrailDecision


def validate_question(question: str) -> GuardrailDecision:
    normalized = question.strip()
    if not normalized or len(normalized) > 2000:
        return GuardrailDecision(
            False,
            "invalid_input",
            "Please provide a non-empty question of at most 2,000 characters.",
        )
    if is_prompt_injection_attempt(normalized):
        return GuardrailDecision(
            False,
            "prompt_injection",
            "I can answer questions about uploaded financial documents, but I can't reveal hidden instructions or change the system rules.",
        )
    if requests_sensitive_personal_data(normalized):
        return GuardrailDecision(
            False,
            "sensitive_personal_data",
            "I can't help extract sensitive personal information. I can help summarize non-sensitive financial information in the uploaded reports.",
        )
    if requests_personalized_investment_advice(normalized):
        return GuardrailDecision(
            False,
            "personalized_investment_advice",
            "I can't make personalized buy, sell, or hold recommendations. I can provide factual information from the uploaded documents.",
        )
    if not is_finance_document_question(normalized):
        return GuardrailDecision(
            False,
            "out_of_scope",
            "I'm designed for questions about uploaded financial documents. Ask about their financial facts, causes, risks, or comparisons.",
        )
    return GuardrailDecision(True, "valid")
