import re

INJECTION_PATTERNS = (
    re.compile(r"\bignore\b.{0,50}\b(previous|prior|above|system|developer)\b.{0,40}\b(instructions?|rules?)\b", re.I),
    re.compile(r"\b(disregard|override|bypass)\b.{0,50}\b(instructions?|rules?|guardrails?|safeguards?)\b", re.I),
    re.compile(r"\b(reveal|print|show|repeat|expose)\b.{0,50}\b(system|developer|hidden)\b.{0,30}\b(prompt|instructions?)\b", re.I),
    re.compile(r"\b(jailbreak|prompt\s+injection)\b", re.I),
)


def is_prompt_injection_attempt(question: str) -> bool:
    return any(pattern.search(question) for pattern in INJECTION_PATTERNS)
