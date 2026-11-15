from functools import lru_cache

from app.core.config import Settings, get_settings
from app.graph.workflow import build_rag_graph
from app.schemas.chat import ChatRequest, ChatResponse


@lru_cache(maxsize=1)
def get_rag_graph():
    return build_rag_graph(get_settings())


def answer_question(request: ChatRequest, settings: Settings, *, user_id: str) -> ChatResponse:
    response, _ = answer_question_with_trace(request, settings, user_id=user_id)
    return response


def answer_question_with_trace(
    request: ChatRequest,
    settings: Settings,
    *,
    user_id: str,
) -> tuple[ChatResponse, list[str]]:
    result = get_rag_graph().invoke(
        {
            "question": request.question,
            "user_id": user_id,
            "filters": request.filters,
            "top_k": request.top_k or settings.retrieval_top_k,
            "retrieved_chunks": [],
            "context": "",
            "answer": "",
            "sources": [],
            "validation_result": "valid",
        }
    )
    response = ChatResponse(answer=result["answer"], sources=result.get("sources", []))
    retrieved_ids = [chunk.chunk_id for chunk in result.get("retrieved_chunks", [])]
    return response, retrieved_ids
