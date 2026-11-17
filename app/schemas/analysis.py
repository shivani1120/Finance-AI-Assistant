from pydantic import BaseModel, Field


class AnalysisDocument(BaseModel):
    document_id: str
    filename: str
    company: str
    reporting_year: int | None = None
    document_type: str
    chunk_count: int = Field(ge=1)


class CompareRequest(BaseModel):
    document_ids: list[str] = Field(min_length=2, max_length=5)


class MetricEvidence(BaseModel):
    value: float
    unit: str = Field(min_length=1, max_length=80)
    quote: str = Field(min_length=1, max_length=1000)
    page_number: int = Field(ge=1)


class FinancialMetric(BaseModel):
    revenue: MetricEvidence | None = None
    operating_profit: MetricEvidence | None = None
    net_income: MetricEvidence | None = None
    operating_cash_flow: MetricEvidence | None = None
    total_debt: MetricEvidence | None = None


class ReportMetrics(BaseModel):
    document_id: str
    filename: str
    company: str
    reporting_year: int | None = None
    document_type: str
    metrics: FinancialMetric
    operating_margin_percent: float | None = None
    revenue_growth_percent: float | None = None


class CompareResponse(BaseModel):
    reports: list[ReportMetrics]
    note: str
