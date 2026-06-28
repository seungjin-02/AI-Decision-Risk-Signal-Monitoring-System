from dataclasses import asdict, is_dataclass
from typing import Any
from app.schemas import EvaluateRequest
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent

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
        event_id = payload.event_id,
        decision_type = payload.decision_type,
        confidence = payload.confidence,
        latency_ms = payload.latency_ms,
        model_version = payload.model_version,
        error_code = payload.error_code,
        metadata = payload.metadata
    )

    try:
        alert_output = evaluate_event(event)
    except ValueError as exc:
        raise CoreValidationException(str(exc)) from exc

    output = _to_dict(alert_output)

    return {
        "trace_id": trace_id,
        "event_id": output["event_id"],
        "level": output["level"],
        "risk_score": output["risk_score"],
        "uncertainty_score": output["uncertainty_score"],
        "human_required": output["human_required"],
        "recommended_actions": output["recommended_actions"],
        "reason_summary": output["reason_summary"],
        "signals": output["signals"],
        "metadata": output.get("metadata", {}),
    }
