from collections.abc import Callable
from datetime import datetime, timezone
from statistics import mean

from app.core.config import Settings
from app.evaluation.dataset import EvaluationCase
from app.evaluation.metrics import citation_metrics, retrieval_metrics, token_f1
from app.rag.retrieval.retriever import retrieve_chunks
from app.schemas.chat import ChatRequest
from app.services.chat_service import answer_question_with_trace

ABSTENTION_MARKERS = (
    "could not find relevant information",
    "do not provide enough information",
    "do not provide enough information to answer",
    "not enough information",
    "could not produce an answer with citations",
)


def _average(values: list[float]) -> float | None:
    return mean(values) if values else None


def evaluate_dataset(
    cases: list[EvaluationCase],
    *,
    settings: Settings,
    top_k: int,
    include_answers: bool,
    answer_runner: Callable = answer_question_with_trace,
) -> dict:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if top_k > settings.retrieval_max_top_k:
        raise ValueError(f"top_k cannot exceed RETRIEVAL_MAX_TOP_K ({settings.retrieval_max_top_k})")
    if include_answers:
        missing_references = [
            case.case_id
            for case in cases
            if case.expected_answerable and not case.reference_answer
        ]
        if missing_references:
            raise ValueError(
                "Answer evaluation needs reference_answer for each answerable case; missing: "
                + ", ".join(missing_references)
            )

    case_reports: list[dict] = []
    retrieval_scores: dict[str, list[float]] = {
        "precision_at_k": [],
        "recall_at_k": [],
        "reciprocal_rank": [],
        "ndcg_at_k": [],
    }
    answer_scores: dict[str, list[float]] = {
        "token_f1": [],
        "citation_precision": [],
        "citation_recall": [],
    }
    answerability_hits: list[float] = []
    valid_citation_rates: list[float] = []

    for case in cases:
        if include_answers:
            request = ChatRequest(
                question=case.question,
                filters=case.filters,
                top_k=top_k,
            )
            response, retrieved_ids = answer_runner(
                request,
                settings,
                user_id=case.user_id,
            )
        else:
            retrieved = retrieve_chunks(
                case.question,
                filters=case.filters,
                user_id=case.user_id,
                top_k=top_k,
                settings=settings,
            )
            retrieved_ids = [chunk.chunk_id for chunk in retrieved]
            response = None

        retrieval = retrieval_metrics(retrieved_ids, case.relevant_chunk_ids, k=top_k)
        for metric, value in retrieval.items():
            if value is not None:
                retrieval_scores[metric].append(value)
        case_report: dict = {
            "case_id": case.case_id,
            "retrieved_chunk_ids": retrieved_ids,
            "retrieval": retrieval,
        }

        if response is not None:
            normalized_answer = response.answer.lower()
            abstained = not response.sources or any(
                marker in normalized_answer for marker in ABSTENTION_MARKERS
            )
            answerability_hits.append(float(abstained == (not case.expected_answerable)))
            source_map = {source.source_id.upper(): source.chunk_id for source in response.sources}
            citations = citation_metrics(response.answer, source_map, case.relevant_chunk_ids)
            valid_citation_rates.append(float(citations["citation_ids_valid"]))
            answer_report: dict = {
                "abstained": abstained,
                "expected_answerable": case.expected_answerable,
                **citations,
            }
            if case.expected_answerable and case.reference_answer is not None:
                score = token_f1(response.answer, case.reference_answer)
                answer_report["token_f1"] = score
                answer_scores["token_f1"].append(score)
                for metric in ("citation_precision", "citation_recall"):
                    answer_scores[metric].append(float(citations[metric]))
            case_report["answer"] = answer_report

        case_reports.append(case_report)

    summary = {metric: _average(values) for metric, values in retrieval_scores.items()}
    if include_answers:
        summary["answerability_accuracy"] = _average(answerability_hits)
        summary["valid_citation_rate"] = _average(valid_citation_rates)
        summary.update({metric: _average(values) for metric, values in answer_scores.items()})

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "top_k": top_k,
        "answer_generation_enabled": include_answers,
        "metrics_note": (
            "Token F1 and citation relevance are lexical/label-based indicators; they do not "
            "prove factual correctness, semantic equivalence, or that a cited passage entails a claim."
        ),
        "summary": summary,
        "cases": case_reports,
    }
