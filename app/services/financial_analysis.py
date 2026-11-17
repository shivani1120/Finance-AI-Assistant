import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import Settings
from app.rag.generation.llm_factory import create_chat_model
from app.rag.ingestion.vector_store import get_chroma_collection
from app.schemas.analysis import AnalysisDocument, FinancialMetric, MetricEvidence, ReportMetrics


class FinancialAnalysisError(RuntimeError):
    """Raised when a report cannot be analyzed safely."""


METRIC_TERMS = {
    "revenue": ("revenue", "turnover", "sales", "income from operations"),
    "operating_profit": ("operating profit", "ebit", "operating income"),
    "net_income": ("net profit", "net income", "profit for the year", "profit after tax"),
    "operating_cash_flow": ("cash generated from operations", "net cash from operating", "operating cash flow"),
    "total_debt": ("total borrowings", "total debt", "borrowings", "loans and borrowings"),
}


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _canonical_unit(unit: str) -> str:
    normalized = re.sub(r"[.,]", "", unit.casefold()).strip()
    normalized = re.sub(r"\brupees?\b|\brs\b|₹", "inr", normalized)
    normalized = re.sub(r"\bcrores\b", "crore", normalized)
    normalized = re.sub(r"\blakhs\b", "lakh", normalized)
    normalized = re.sub(r"\bmillions\b", "million", normalized)
    normalized = re.sub(r"\bbillions\b", "billion", normalized)
    return " ".join(normalized.split())


def _currency_code(unit: str) -> str | None:
    normalized = unit.casefold()
    currencies = {
        "inr": ("inr", "₹", "rupee", "rs."),
        "usd": ("usd", "us$"),
        "eur": ("eur", "€", "euro"),
        "gbp": ("gbp", "£", "pound sterling"),
        "jpy": ("jpy", "jp¥", "yen"),
        "cny": ("cny", "rmb", "cn¥", "yuan"),
    }
    for code, markers in currencies.items():
        if any(marker in normalized for marker in markers):
            return code
    return None


def _read_user_chunks(
    user_id: str,
    settings: Settings,
    *,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    collection = get_chroma_collection(settings)
    where: dict[str, Any] = {"user_id": user_id}
    if document_id is not None:
        where = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}
    result = collection.get(
        where=where,
        include=["documents", "metadatas"],
    )
    ids = result.get("ids") or []
    texts = result.get("documents") or []
    metadata = result.get("metadatas") or []
    chunks: list[dict[str, Any]] = []
    for chunk_id, text, meta in zip(ids, texts, metadata, strict=False):
        if text and meta:
            chunks.append({"id": str(chunk_id), "text": text, "metadata": meta})
    return chunks


def list_user_documents(user_id: str, settings: Settings) -> list[AnalysisDocument]:
    grouped: dict[str, dict[str, Any]] = {}
    for chunk in _read_user_chunks(user_id, settings):
        meta = chunk["metadata"]
        document_id = str(meta.get("document_id", ""))
        if not document_id:
            continue
        entry = grouped.setdefault(
            document_id,
            {
                "document_id": document_id,
                "filename": str(meta.get("filename", "Report")),
                "company": str(meta.get("company", "Unknown company")),
                "reporting_year": meta.get("reporting_year"),
                "document_type": str(meta.get("document_type", "other")),
                "chunk_count": 0,
            },
        )
        entry["chunk_count"] += 1
    documents = [AnalysisDocument(**item) for item in grouped.values()]
    return sorted(documents, key=lambda doc: (doc.company.casefold(), doc.reporting_year or 0, doc.filename.casefold()))


def _select_evidence_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Keep the best passages for each requested metric, while retaining page and exact text
    # so the returned extraction can be checked against its source.
    chosen: dict[str, dict[str, Any]] = {}
    for metric, terms in METRIC_TERMS.items():
        scored: list[tuple[int, dict[str, Any]]] = []
        for chunk in chunks:
            content = chunk["text"].casefold()
            score = sum(content.count(term) for term in terms)
            if score:
                scored.append((score, chunk))
        for _, chunk in sorted(scored, key=lambda pair: pair[0], reverse=True)[:4]:
            chosen[chunk["id"]] = chunk
    if not chosen:
        chosen = {chunk["id"]: chunk for chunk in chunks[:12]}
    return list(chosen.values())[:20]


def _response_text(response: Any) -> str:
    if isinstance(response.content, str):
        return response.content.strip()
    return "\n".join(
        block["text"]
        for block in response.content
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
    ).strip()


def _extract_metrics(chunks: list[dict[str, Any]], settings: Settings) -> FinancialMetric:
    evidence_chunks = _select_evidence_chunks(chunks)
    source_text = "\n\n".join(
        f"[page {chunk['metadata'].get('page_number')} | chunk {chunk['id']}]\n{chunk['text']}"
        for chunk in evidence_chunks
    )
    prompt = (
        "Extract these financial figures if explicitly stated: revenue, operating_profit, "
        "net_income, operating_cash_flow, total_debt. Return JSON only with this shape: "
        '{"revenue":{"value":123.0,"unit":"INR crore","quote":"exact source wording with value","page_number":12},'
        '"operating_profit":null,"net_income":null,"operating_cash_flow":null,"total_debt":null}. '
        "The value must be numeric in the report's displayed units; include currency and scale in unit, "
        "do not convert units or infer missing values. "
        "The quote must be copied exactly from one supplied chunk and include the amount. The page number must "
        "be the page printed in that chunk header. Prefer consolidated statements and compare figures only when "
        "they share the same statement basis and reporting period. If labels, units, basis, or values are ambiguous, return null."
    )
    model = create_chat_model(settings)
    try:
        response = model.invoke(
            [SystemMessage(content=prompt), HumanMessage(content=source_text)]
        )
        raw = _response_text(response)
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return FinancialMetric()
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return FinancialMetric()
        if not isinstance(payload, dict):
            return FinancialMetric()
        checked: dict[str, MetricEvidence | None] = {}
        for metric in METRIC_TERMS:
            item = payload.get(metric)
            if not isinstance(item, dict):
                checked[metric] = None
                continue
            try:
                candidate = MetricEvidence.model_validate(item)
            except Exception:
                checked[metric] = None
                continue
            quoted = _normalize(candidate.quote)
            numeric = format(candidate.value, ".12g")
            source_numbers = re.findall(r"(?<!\w)-?\d[\d,]*(?:\.\d+)?", candidate.quote)
            source_numbers = [number.replace(",", "") for number in source_numbers]
            quote_matches_page = any(
                candidate.page_number == int(chunk["metadata"].get("page_number", 0))
                and quoted in _normalize(chunk["text"])
                for chunk in evidence_chunks
            )
            if (
                not quoted
                or not quote_matches_page
                or not any(format(float(number), ".12g") == numeric for number in source_numbers)
            ):
                checked[metric] = None
                continue
            checked[metric] = candidate
        return FinancialMetric(**checked)
    except Exception as exc:
        raise FinancialAnalysisError("Could not extract figures from the selected report") from exc


def compare_user_reports(
    document_ids: list[str], *, user_id: str, settings: Settings
) -> list[ReportMetrics]:
    if len(set(document_ids)) != len(document_ids):
        raise ValueError("Choose each report only once")
    by_document = {
        document_id: _read_user_chunks(user_id, settings, document_id=document_id)
        for document_id in document_ids
    }
    if any(not chunks for chunks in by_document.values()):
        raise LookupError("One or more reports were not found in your account")

    reports: list[ReportMetrics] = []
    for document_id in document_ids:
        chunks = by_document[document_id]
        metadata = chunks[0]["metadata"]
        metrics = _extract_metrics(chunks, settings)
        margin = None
        revenue = metrics.revenue
        operating_profit = metrics.operating_profit
        if (
            revenue
            and operating_profit
            and revenue.value != 0
            and _canonical_unit(revenue.unit) == _canonical_unit(operating_profit.unit)
        ):
            margin = round(operating_profit.value / revenue.value * 100, 2)
        reports.append(
            ReportMetrics(
                document_id=document_id,
                filename=str(metadata.get("filename", "Report")),
                company=str(metadata.get("company", "Unknown company")),
                reporting_year=metadata.get("reporting_year"),
                document_type=str(metadata.get("document_type", "other")),
                metrics=metrics,
                operating_margin_percent=margin,
            )
        )

    by_company: dict[str, list[ReportMetrics]] = {}
    for report in reports:
        by_company.setdefault(report.company.casefold(), []).append(report)
    for company_reports in by_company.values():
        ordered = sorted(company_reports, key=lambda report: report.reporting_year or 0)
        for prior, current in zip(ordered, ordered[1:]):
            old, new = prior.metrics.revenue, current.metrics.revenue
            if (
                old
                and new
                and old.value != 0
                and _canonical_unit(old.unit) == _canonical_unit(new.unit)
                and _currency_code(old.unit) is not None
                and _currency_code(old.unit) == _currency_code(new.unit)
                and prior.document_type == "annual_report"
                and current.document_type == "annual_report"
                and current.reporting_year != prior.reporting_year
            ):
                current.revenue_growth_percent = round((new.value - old.value) / abs(old.value) * 100, 2)
    return sorted(reports, key=lambda report: (report.company.casefold(), report.reporting_year or 0))
