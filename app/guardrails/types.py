from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    category: str
    message: str | None = None


@dataclass(frozen=True)
class OutputDecision:
    accepted: bool
    category: str
