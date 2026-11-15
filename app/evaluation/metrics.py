import re
from collections import Counter
from math import log2


def retrieval_metrics(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    *,
    k: int,
) -> dict[str, float | None]:
    relevant = set(relevant_ids)
    ranked = retrieved_ids[:k]
    hits = [1 if chunk_id in relevant else 0 for chunk_id in ranked]
    first_relevant_rank = next((rank for rank, hit in enumerate(hits, start=1) if hit), None)

    dcg = sum(hit / log2(rank + 1) for rank, hit in enumerate(hits, start=1))
    ideal_hits = min(len(relevant), k)
    idcg = sum(1 / log2(rank + 1) for rank in range(1, ideal_hits + 1))

    return {
        "precision_at_k": sum(hits) / k,
        "recall_at_k": sum(hits) / len(relevant) if relevant else None,
        "reciprocal_rank": 1 / first_relevant_rank if first_relevant_rank else 0.0,
        "ndcg_at_k": dcg / idcg if idcg else 0.0,
    }


def token_f1(prediction: str, reference: str) -> float:
    """A lexical overlap score for rough regression checks, not semantic correctness."""
    strip_citations = lambda text: re.sub(r"\[S\d+\]", " ", text, flags=re.I)
    tokenize = lambda text: re.findall(
        r"[a-z0-9]+(?:\.[0-9]+)?", strip_citations(text).lower()
    )
    predicted_tokens = Counter(tokenize(prediction))
    reference_tokens = Counter(tokenize(reference))
    if not predicted_tokens or not reference_tokens:
        return float(predicted_tokens == reference_tokens)
    overlap = sum((predicted_tokens & reference_tokens).values())
    if not overlap:
        return 0.0
    precision = overlap / sum(predicted_tokens.values())
    recall = overlap / sum(reference_tokens.values())
    return 2 * precision * recall / (precision + recall)


def citation_metrics(
    answer: str,
    source_map: dict[str, str],
    relevant_ids: list[str],
) -> dict[str, float | bool]:
    cited_ids = {source_id.upper() for source_id in re.findall(r"\[(S\d+)\]", answer, re.I)}
    valid = cited_ids.issubset(source_map)
    cited_chunks = {source_map[source_id] for source_id in cited_ids if source_id in source_map}
    relevant = set(relevant_ids)
    relevant_cited = cited_chunks & relevant
    return {
        "citation_ids_valid": valid,
        "citation_precision": len(relevant_cited) / len(cited_chunks) if cited_chunks else 0.0,
        "citation_recall": len(relevant_cited) / len(relevant) if relevant else 0.0,
    }
