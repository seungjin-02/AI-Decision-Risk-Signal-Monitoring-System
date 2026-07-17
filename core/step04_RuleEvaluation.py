from dataclasses import dataclass, field
from typing import Any, Callable

from .step02_NormalizedEvent import NormalizedEvent
from .step03_EvaluationContext import EvaluationContext

RuleCondition = Callable[[NormalizedEvent, dict[str, Any], EvaluationContext], bool]

@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    condition: RuleCondition
    score: int
    reason: str
    evidence_fields: list[str] = field(default_factory=list)
    is_critical_override: bool = False
    thresholds: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class RuleEvaluation:
    rule: Rule
    triggered: bool

def check_approve_confidence_low(
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    if event.decision_type != "approve":
        return False
    if event.confidence is None:
        return False

    return event.confidence <= thresholds["confidence"]

def check_latency_high (
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    if event.latency_ms is None:
        return False

    return event.latency_ms >= thresholds["latency_ms"]

def check_missing_confidence(
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    return "confidence" in context.missing_fields

def check_missing_model_version(
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    return "model_version" in context.missing_fields

def check_evaluation_integrity_failure(
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    if event.error_code is None:
        return False

    critical_override_error_codes = thresholds.get("error_codes", [])
    return event.error_code in critical_override_error_codes

def check_stability_signal(
    event: NormalizedEvent,
    thresholds: dict[str, Any],
    context: EvaluationContext
) -> bool:
    return False

RULES: list[Rule] = [
    Rule(
        rule_id = "approve_confidence_low",
        category = "risk",
        condition = check_approve_confidence_low,
        score = 3,
        reason = "approve decision with low confidence",
        evidence_fields = ["decision_type", "confidence"],
        is_critical_override= False,
        thresholds = {"confidence": 0.6}
    ),
    Rule(
        rule_id = "latency_high",
        category = "risk",
        condition = check_latency_high,
        score = 2,
        reason = "response latency exceeded threshold",
        evidence_fields = ["latency_ms"],
        is_critical_override= False,
        thresholds = {"latency_ms": 2000}
    ),
    Rule(
        rule_id = "missing_confidence",
        category = "uncertainty",
        condition = check_missing_confidence,
        score = 1,
        reason = "confidence field is missing",
        evidence_fields = ["confidence"],
        is_critical_override= False,
        thresholds = {}
    ),
    Rule(
        rule_id = "missing_model_version",
        category = "uncertainty",
        condition = check_missing_model_version,
        score = 1,
        reason = "model_version field is missing",
        evidence_fields = ["model_version"],
        is_critical_override= False,
        thresholds = {}
    ),
    Rule(
        rule_id = "evaluation_integrity_override",
        category = "failure",
        condition = check_evaluation_integrity_failure,
        score = 0,
        reason = "evaluation integrity failure requires critical review",
        evidence_fields = ["error_code"],
        is_critical_override = True,
        thresholds = {"error_codes": ["timeout_01", "gateway_failure"]},
        metadata = {
            "failure_type": "system_error",
            "score_contribution": "none",
            "override_type": "critical",
        },
    ),
    Rule(
        rule_id = "stability_signal",
        category = "stability",
        condition = check_stability_signal,
        score = 0,
        reason = "stability signal detected",
        evidence_fields = [],
        is_critical_override= False,
        thresholds = {}
    )
]

def evaluate_rule(
    event: NormalizedEvent,
    context: EvaluationContext,
    rules: list[Rule] | None = None,
) -> list[RuleEvaluation]:
    active_rules = rules if rules is not None else RULES
    evaluations: list[RuleEvaluation] = []

    for rule in active_rules:
        triggered = rule.condition(event, rule.thresholds, context)
        evaluations.append(
            RuleEvaluation(
                rule = rule,
                triggered = triggered
            )
        )
    return evaluations
