from dataclasses import dataclass, field
from typing import Any
from .step01_DecisionEvent import DecisionEvent

@dataclass(frozen=True)
class ValidationIssue:
    field_name: str
    message: str
    value: Any = None

@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

def validate_event(event: DecisionEvent) -> ValidationResult:
    issues: list[ValidationIssue] = []

    _validate_event_id(event, issues)
    _validate_confidence(event, issues)
    _validate_latency_ms(event, issues)
    _validate_decision_type(event, issues)
    _validate_model_version(event, issues)
    _validate_error_code(event, issues)
    _validate_metadata(event, issues)

    return ValidationResult(is_valid = len(issues) == 0, issues = issues)

def _validate_event_id(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if event.event_id is None:
        issues.append(
            ValidationIssue(
                field_name = "event_id",
                message = "event_id is required",
                value = event.event_id
            )
        )
        return

    if not isinstance(event.event_id, str):
        issues.append(
            ValidationIssue(
                field_name = "event_id",
                message = "event_id must be a string",
                value = event.event_id
            )
        )
        return

    if event.event_id.strip() == "":
        issues.append(
            ValidationIssue(
                field_name = "event_id",
                message = "event_id must not be empty",
                value = event.event_id
            )
        )

def _validate_confidence(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if event.confidence is None:
        return

    if isinstance(event.confidence, bool) or not isinstance(event.confidence, (int, float)):
        issues.append(
            ValidationIssue(
                field_name = "confidence",
                message = "confidence must be an number between 0.0 and 1.0",
                value = event.confidence
            )
        )
        return

    if not 0.0 <= event.confidence <= 1.0:
        issues.append(
            ValidationIssue(
                field_name = "confidence",
                message = "confidence must be between 0.0 and 1.0",
                value = event.confidence
            )
        )

def _validate_latency_ms(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if event.latency_ms is None:
        return

    if isinstance(event.latency_ms, bool) or not isinstance(event.latency_ms, int):
        issues.append(
            ValidationIssue(
                field_name = "latency_ms",
                message = "latency ms must be an integer",
                value = event.latency_ms
            )
        )
        return

    if event.latency_ms < 0:
        issues.append(
            ValidationIssue(
                field_name = "latency_ms",
                message = "latency ms must be greater than or equal to zero",
                value = event.latency_ms

            )
        )

def _validate_decision_type(
    event: DecisionEvent,
    issues: list[ValidationIssue],
) -> None:
    if event.decision_type is None:
        return

    if not isinstance(event.decision_type, str):
        issues.append(
            ValidationIssue(
                field_name = "decision_type",
                message = "decision_type must be a string",
                value = event.decision_type
            )
        )
        return

    normalized_decision_type = event.decision_type.strip().lower()

    if normalized_decision_type == "":
        issues.append(
            ValidationIssue(
                field_name = "decision_type",
                message = "decision_type cannot be empty",
                value = event.decision_type
            )
        )
        return

    if normalized_decision_type not in {"approve", "reject"}:
        issues.append(
            ValidationIssue(
                field_name = "decision_type",
                message = "decision_type must be one of: approve, reject",
                value = event.decision_type
            )
        )

def _validate_model_version(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if event.model_version is None:
        return

    if not isinstance(event.model_version, str):
        issues.append(
            ValidationIssue(
                field_name="model_version",
                message="model_version must be a string",
                value=event.model_version,
            )
        )

def _validate_error_code(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if event.error_code is None:
        return

    if not isinstance(event.error_code, str):
        issues.append(
            ValidationIssue(
                field_name="error_code",
                message="error_code must be a string",
                value=event.error_code,
            )
        )

def _validate_metadata(
    event: DecisionEvent,
    issues: list[ValidationIssue]
) -> None:
    if not isinstance(event.metadata, dict):
        issues.append(
            ValidationIssue(
                field_name = "metadata",
                message = "metadata must be a dictionary",
                value = event.metadata,
            )
        )

def format_validation_issues(issues: list[ValidationIssue]) -> str:
    return "; ".join(f"{issue.field_name}: {issue.message} (value={issue.value})" for issue in issues)
