import re

from app.schemas.chat import ChatSource

CITATION_PATTERN = re.compile(r"\[(S\d+)\]", re.I)


def validate_citation_ids(answer: str, sources: list[ChatSource]) -> bool:
    available = {source.source_id.upper() for source in sources}
    cited = {citation.upper() for citation in CITATION_PATTERN.findall(answer)}
    return cited.issubset(available)
