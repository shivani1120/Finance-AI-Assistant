import re

PERSONAL_RECOMMENDATION_PATTERNS = (
    re.compile(r"\b(?:you should|you ought to|i recommend|my advice is)\s+(?:buy|sell|hold|purchase|invest|trade)\b", re.I),
    re.compile(r"\bthis\s+(?:stock|share|investment)\s+is\s+a\s+(?:buy|sell|hold)\b", re.I),
)


def contains_personalized_recommendation(answer: str) -> bool:
    return any(pattern.search(answer) for pattern in PERSONAL_RECOMMENDATION_PATTERNS)
