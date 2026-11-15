import re

FINANCE_SCOPE_PATTERN = re.compile(
    r"\b(financial|finance|revenue|sales|income|earnings|profit|loss|margin|"
    r"cash\s+flow|balance\s+sheet|asset|liabilit\w*|debt|dividend|equity|"
    r"stock|share|market\s+cap|investor|annual\s+report|quarterly\s+report|"
    r"10-k|10-q|financial\s+statement|company|business|accounting|risk|risks|"
    r"guidance|operating|expense|report|document|filing)\b",
    re.I,
)


def is_finance_document_question(question: str) -> bool:
    return bool(FINANCE_SCOPE_PATTERN.search(question))
