from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class DecisionEvent:
    event_id: str
    decision_type: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    model_version: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory = dict)
