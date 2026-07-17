from dataclasses import dataclass, field

from .step02_NormalizedEvent import NormalizedEvent

@dataclass(frozen=True)
class EvaluationContext:
    missing_fields: list[str] = field(default_factory=list)
    evaluation_limits: list[str] = field(default_factory=list)
    field_presence: dict[str, bool] = field(default_factory=dict)

def build_evaluation_context(event: NormalizedEvent) -> EvaluationContext:
    missing_fields: list[str] = []
    evaluation_limits: list[str] = []
    field_presence: dict[str, bool] = {}
    tracked_fields = {
        "decision_type": event.decision_type,
        "confidence": event.confidence,
        "latency_ms": event.latency_ms,
        "model_version": event.model_version,
        "error_code": event.error_code
    }
    missing_sensitive_fields = {
        "decision_type",
        "confidence",
        "latency_ms",
        "model_version"
    }

    for field_name, value in tracked_fields.items():
        is_present = value is not None
        field_presence[field_name] = is_present
        if not is_present and field_name in missing_sensitive_fields:
            missing_fields.append(field_name)

    if "confidence" in missing_fields:
        evaluation_limits.append("approve_confidence_rule_blocked")

    if "decision_type" in missing_fields:
        evaluation_limits.append("decision_type_dependent_rules_blocked")

    return EvaluationContext(
        missing_fields = missing_fields,
        evaluation_limits = evaluation_limits,
        field_presence = field_presence,
    )