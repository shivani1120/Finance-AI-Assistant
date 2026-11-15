import re

PERSONAL_ADVICE_PATTERNS = (
    re.compile(r"\bshould\s+i\s+(buy|sell|hold|purchase|invest|trade)\b", re.I),
    re.compile(r"\bwhat\s+should\s+i\s+invest\s+in\b", re.I),
    re.compile(r"\b(?:can|could|would)\s+you\s+recommend\b.{0,60}\b(me|stock|share|investment|portfolio|buy|sell)\b", re.I),
    re.compile(r"\b(?:recommend|suggest)\b.{0,60}\b(?:for\s+me|my\s+portfolio|a\s+stock|an?\s+investment)\b", re.I),
)


def requests_personalized_investment_advice(question: str) -> bool:
    return any(pattern.search(question) for pattern in PERSONAL_ADVICE_PATTERNS)
