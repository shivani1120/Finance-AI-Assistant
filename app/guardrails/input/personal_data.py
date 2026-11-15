import re

SENSITIVE_DATA_REQUEST_PATTERNS = (
    re.compile(r"\b(social\s+security|ssn|taxpayer\s+identification)\s+(number|id)\b", re.I),
    re.compile(r"\b(passport|driver'?s\s+license|credit\s+card|debit\s+card|bank\s+account|routing)\s+(number|details?)\b", re.I),
    re.compile(r"\b(personal|private)\s+(email|phone|address|contact|financial)\s+(address|number|details?|information)?\b", re.I),
    re.compile(r"\b(home\s+address|personal\s+phone\s+number|private\s+email\s+address)\b", re.I),
    re.compile(r"\b(sensitive\s+personal\s+(data|information)|private\s+information)\b", re.I),
)


def requests_sensitive_personal_data(question: str) -> bool:
    return any(pattern.search(question) for pattern in SENSITIVE_DATA_REQUEST_PATTERNS)
