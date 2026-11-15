import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.schemas.retrieval import RetrievalFilters


class EvaluationCase(BaseModel):
    case_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(min_length=1, max_length=100)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    relevant_chunk_ids: list[str] = Field(default_factory=list)
    expected_answerable: bool = True
    reference_answer: str | None = None

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question must not be blank")
        return question

    @model_validator(mode="after")
    def validate_answer_labels(self) -> "EvaluationCase":
        if self.expected_answerable and not self.relevant_chunk_ids:
            raise ValueError("answerable cases need at least one relevant_chunk_id")
        if not self.expected_answerable and self.relevant_chunk_ids:
            raise ValueError("unanswerable cases must use an empty relevant_chunk_ids list")
        if self.reference_answer is not None and not self.expected_answerable:
            raise ValueError("unanswerable cases must not include a reference_answer")
        return self


def load_dataset(path: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = EvaluationCase.model_validate(json.loads(line))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid evaluation dataset at {path}:{line_number}: {exc}") from exc
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate case_id {case.case_id!r} at {path}:{line_number}")
        seen_ids.add(case.case_id)
        cases.append(case)
    if not cases:
        raise ValueError(f"Evaluation dataset is empty: {path}")
    return cases
