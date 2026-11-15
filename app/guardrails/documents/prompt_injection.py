import re

from app.schemas.retrieval import RetrievedChunk

DOCUMENT_INJECTION_PATTERNS = (
    re.compile(r"\bignore\b.{0,60}\b(previous|prior|system|developer)\b.{0,40}\b(instructions?|rules?)\b", re.I),
    re.compile(r"\b(disregard|override|bypass)\b.{0,50}\b(system\s+)?(instructions?|rules?|guardrails?)\b", re.I),
    re.compile(r"\b(reveal|print|show|expose)\b.{0,50}\b(system|developer|hidden)\b.{0,30}\b(prompt|instructions?)\b", re.I),
    re.compile(r"\b(send|return|exfiltrate)\b.{0,50}\b(api\s+keys?|secrets?|credentials?)\b", re.I),
)


def contains_embedded_instructions(text: str) -> bool:
    return any(pattern.search(text) for pattern in DOCUMENT_INJECTION_PATTERNS)


def remove_unsafe_chunks(chunks: list[RetrievedChunk]) -> tuple[list[RetrievedChunk], int]:
    safe_chunks: list[RetrievedChunk] = []
    removed_count = 0
    for chunk in chunks:
        if contains_embedded_instructions(chunk.content):
            removed_count += 1
        else:
            safe_chunks.append(chunk)
    return safe_chunks, removed_count
