from langchain_core.prompts import ChatPromptTemplate

from app.core.config import Settings
from app.rag.generation.llm_factory import create_chat_model
from app.rag.prompts.finance_rag import HUMAN_PROMPT, SYSTEM_PROMPT


class AnswerGenerationError(RuntimeError):
    """Raised when the configured LLM fails to produce a usable answer."""


INTENT_INSTRUCTIONS = {
    "financial_fact": "Give the requested fact and its reporting period if present.",
    "causal_explanation": (
        "Describe only drivers the documents state. Do not turn timing or correlation into causation."
    ),
    "comparison": (
        "Compare only periods or companies present in the excerpts, and keep their labels distinct."
    ),
    "risk_summary": "Summarize risks stated in the excerpts without predicting their likelihood.",
}


def generate_grounded_answer(
    question: str,
    intent: str,
    context: str,
    settings: Settings,
) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
    )
    messages = prompt.format_messages(
        question=question,
        intent_instruction=INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["financial_fact"]),
        context=context,
    )

    model = create_chat_model(settings)
    try:
        response = model.invoke(messages)
    except Exception as exc:
        raise AnswerGenerationError("The configured LLM could not generate an answer") from exc

    if isinstance(response.content, str):
        answer = response.content.strip()
    else:
        text_parts = [
            block["text"]
            for block in response.content
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
        ]
        answer = "\n".join(text_parts).strip()

    if not answer:
        raise AnswerGenerationError("The configured LLM returned an empty answer")
    return answer
