from step01_DecisionEvent import DecisionEvent
from step02_NormalizedEvent import normalize_event
from step03_EvaluationContext import build_evaluation_context
from step04_RuleEvaluation import evaluate_rule

def evaluate_event_rules(event: DecisionEvent):
    normalized = normalize_event(event)
    context = build_evaluation_context(event)
    return evaluate_rule(normalized, context)

def is_rule_triggered(evaluations, rule_id: str) -> bool:
    return any(
        evaluation.rule.rule_id == rule_id and evaluation.triggered for evaluation in evaluations
    )

def test_approve_confidence_low_triggered_at_threshold():
    event = DecisionEvent(
        event_id="evt_rule_001",
        decision_type="approve",
        confidence=0.6,
        latency_ms=800,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert is_rule_triggered(evaluations, "approve_confidence_low")

def test_approve_confidence_low_not_triggered_above_threshold():
    event = DecisionEvent(
        event_id="evt_rule_002",
        decision_type="approve",
        confidence=0.61,
        latency_ms=800,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert not is_rule_triggered(evaluations, "approve_confidence_low")

def test_approve_confidence_low_not_triggered_for_reject():
    event = DecisionEvent(
        event_id="evt_rule_003",
        decision_type="reject",
        confidence=0.4,
        latency_ms=800,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert not is_rule_triggered(evaluations, "approve_confidence_low")

def test_latency_high_triggered_at_threshold():
    event = DecisionEvent(
        event_id="evt_rule_004",
        decision_type="approve",
        confidence=0.9,
        latency_ms=2000,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert is_rule_triggered(evaluations, "latency_high")

def test_latency_high_not_triggered_below_threshold():
    event = DecisionEvent(
        event_id="evt_rule_005",
        decision_type="approve",
        confidence=0.9,
        latency_ms=1999,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert not is_rule_triggered(evaluations, "latency_high")

def test_missing_model_version_triggered():
    event = DecisionEvent(
        event_id="evt_rule_006",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version=None,
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert is_rule_triggered(evaluations, "missing_model_version")

def test_missing_confidence_triggered():
    event = DecisionEvent(
        event_id="evt_rule_007",
        decision_type="approve",
        confidence=None,
        latency_ms=800,
        model_version="v1",
        error_code=None,
    )

    evaluations = evaluate_event_rules(event)
    assert is_rule_triggered(evaluations, "missing_confidence")

def test_system_error_override_triggered_for_gateway_failure():
    event = DecisionEvent(
        event_id="evt_rule_008",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version="v1",
        error_code="gateway_failure",
    )

    evaluations = evaluate_event_rules(event)
    assert is_rule_triggered(evaluations, "system_error_override")

def test_system_error_override_not_triggered_for_unknown_error():
    event = DecisionEvent(
        event_id="evt_rule_009",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version="v1",
        error_code="unknown_error",
    )

    evaluations = evaluate_event_rules(event)
    assert not is_rule_triggered(evaluations, "system_error_override")