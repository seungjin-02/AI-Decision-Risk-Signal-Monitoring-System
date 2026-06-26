from dataclasses import asdict, is_dataclass
from typing import Any

from app.schemas import EvaluateRequest
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent


FORBIDDEN_RESPONSE_FIELDS = {
    "priority",
    "combined_score",
    "final_decision",
    "auto_approve",
    "auto_reject",
    "approval_result",
    "rejection_result",
}


class CoreValidationException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _to_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)

    raise TypeError(f"Object is not serializable: {type(obj)}")


def evaluate_request(payload: EvaluateRequest, trace_id: str) -> dict[str, Any]:
    event = DecisionEvent(
        event_id=payload.event_id,
        decision_type=payload.decision_type,
        confidence=payload.confidence,
        latency_ms=payload.latency_ms,
        model_version=payload.model_version,
        error_code=payload.error_code,
        metadata=payload.metadata,
    )

    try:
        alert_output = evaluate_event(event)
    except ValueError as exc:
        raise CoreValidationException(str(exc)) from exc

    response = {
        "trace_id": trace_id,
        **_to_dict(alert_output),
    }

    for field in FORBIDDEN_RESPONSE_FIELDS:
        response.pop(field, None)

    return response