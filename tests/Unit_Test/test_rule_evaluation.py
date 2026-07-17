from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context
from core.step04_RuleEvaluation import RULES, evaluate_rule

def test_all_default_rules():
    event = DecisionEvent(
        event_id = "evt_rule_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert len(evaluations) == len(RULES)
    assert [evaluation.rule.rule_id for evaluation in evaluations] == [rule.rule_id for rule in RULES]

def test_approve_confidence_low_triggered_at_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_002",
        decision_type = "approve",
        confidence = 0.6,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "approve_confidence_low" and evaluation.triggered for evaluation in evaluations
    )

def test_approve_confidence_low_triggered_below_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_003",
        decision_type = "approve",
        confidence = 0.59,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "approve_confidence_low" and evaluation.triggered for evaluation in evaluations
    )


def test_approve_confidence_low_not_triggered_above_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_004",
        decision_type = "approve",
        confidence = 0.61,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "approve_confidence_low" and evaluation.triggered for evaluation in evaluations
    )

def test_approve_confidence_low_not_triggered_for_reject_decision():
    event = DecisionEvent(
        event_id = "evt_rule_005",
        decision_type = "reject",
        confidence = 0.4,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "approve_confidence_low" and evaluation.triggered for evaluation in evaluations
    )


def test_approve_confidence_low_not_triggered_when_confidence_missing():
    event = DecisionEvent(
        event_id = "evt_rule_006",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "approve_confidence_low" and evaluation.triggered for evaluation in evaluations
    )
    assert any(
        evaluation.rule.rule_id == "missing_confidence" and evaluation.triggered for evaluation in evaluations
    )

def test_latency_high_triggered_at_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_007",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2000,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "latency_high" and evaluation.triggered for evaluation in evaluations
    )

def test_latency_high_triggered_above_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_008",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "latency_high" and evaluation.triggered for evaluation in evaluations
    )

def test_latency_high_not_triggered_below_threshold():
    event = DecisionEvent(
        event_id = "evt_rule_009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 1999,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "latency_high" and evaluation.triggered for evaluation in evaluations
    )

def test_latency_high_not_triggered_when_latency_missing():
    event = DecisionEvent(
        event_id = "evt_rule_010",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = None,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "latency_high" and evaluation.triggered for evaluation in evaluations
    )


def test_missing_confidence_triggered():
    event = DecisionEvent(
        event_id = "evt_rule_011",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "missing_confidence" and evaluation.triggered for evaluation in evaluations
    )


def test_missing_model_version_triggered_when_model_version_none():
    event = DecisionEvent(
        event_id = "evt_rule_012",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "missing_model_version" and evaluation.triggered for evaluation in evaluations
    )


def test_missing_model_version_triggered_when_model_version_blank():
    event = DecisionEvent(
        event_id = "evt_rule_013",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "   ",
        error_code = None,
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "missing_model_version" and evaluation.triggered for evaluation in evaluations
    )

def test_evaluation_integrity_override_triggered_for_gateway_failure():
    event = DecisionEvent(
        event_id = "evt_rule_014",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "evaluation_integrity_override" and evaluation.triggered for evaluation in evaluations
    )


def test_evaluation_integrity_override_triggered_for_timeout():
    event = DecisionEvent(
        event_id = "evt_rule_015",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "timeout_01"
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert any(
        evaluation.rule.rule_id == "evaluation_integrity_override" and evaluation.triggered for evaluation in evaluations
    )

def test_evaluation_integrity_override_not_triggered_for_unknown_error():
    event = DecisionEvent(
        event_id = "evt_rule_016",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "unknown_error"
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "evaluation_integrity_override" and evaluation.triggered for evaluation in evaluations
    )

def test_stability_signal_is_not_triggered_by_default():
    event = DecisionEvent(
        event_id = "evt_rule_017",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)

    assert not any(
        evaluation.rule.rule_id == "stability_signal" and evaluation.triggered for evaluation in evaluations
    )