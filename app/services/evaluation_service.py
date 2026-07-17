from typing import Any
from app.schemas import EvaluateRequest
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent
from core.step05_SignalGeneration import Signal
from core.step09_AlertOutput import AlertOutput

class CoreValidationException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def build_decision_event(payload: EvaluateRequest) -> DecisionEvent:
    return DecisionEvent(
        event_id = payload.event_id,
        decision_type = payload.decision_type,
        confidence = payload.confidence,
        latency_ms = payload.latency_ms,
        model_version = payload.model_version,
        error_code = payload.error_code,
        metadata = payload.metadata
    )

def signal_to_response(signal: Signal) -> dict[str, Any]:
    return {
        "rule_id": signal.rule_id,
        "category": signal.category,
        "score": signal.score,
        "reason": signal.reason,
        "evidence": signal.evidence,
        "is_critical_override": signal.is_critical_override,
        "metadata": signal.metadata
    }

def alert_to_response(alert: AlertOutput, trace_id: str) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "event_id": alert.event_id,
        "level": alert.level,
        "risk_score": alert.risk_score,
        "uncertainty_score": alert.uncertainty_score,
        "human_required": alert.human_required,
        "recommended_actions": alert.recommended_actions,
        "reason_summary": alert.reason_summary,
        "signals": [
            signal_to_response(signal) for signal in alert.signals
        ],
        "metadata": alert.metadata
    }

def evaluate_request(payload: EvaluateRequest, trace_id: str) -> dict[str, Any]:
    event = build_decision_event(payload)
    try:
        alert = evaluate_event(event)
    except ValueError as exc:
        raise CoreValidationException(str(exc)) from exc

    return alert_to_response(alert, trace_id)