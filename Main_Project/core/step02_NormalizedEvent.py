from dataclasses import dataclass, field
from typing import Any
from step01_DecisionEvent import DecisionEvent

@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    decision_type: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    model_version: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

def _normalize_optional_str(value: str | None, *, lowercase: bool = False) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        return None

    return normalized.lower() if lowercase else normalized

def _normalize_optional_float(value: float | int | str | None) -> float | None:
    if value is None:
        return None
    return float(value)

def _normalize_optional_int(value: int | float | str | None) -> int | None:
    if value is None:
        return None
    return int(value)

def normalize_event(event: DecisionEvent) -> NormalizedEvent:
    return NormalizedEvent(
        event_id = event.event_id.strip(),
        decision_type = _normalize_optional_str(event.decision_type, lowercase=True),
        confidence = _normalize_optional_float(event.confidence),
        latency_ms = _normalize_optional_int(event.latency_ms),
        model_version = _normalize_optional_str(event.model_version),
        error_code = _normalize_optional_str(event.error_code, lowercase=True),
        metadata = dict(event.metadata)
    )












