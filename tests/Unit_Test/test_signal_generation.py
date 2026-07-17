from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context
from core.step04_RuleEvaluation import evaluate_rule
from core.step05_SignalGeneration import build_signals

def test_no_signal_when_no_rules_triggered():
    event = DecisionEvent(
        event_id = "evt_signal_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert signals == []

def test_low_confidence_signal():
    event = DecisionEvent(
        event_id = "evt_signal_002",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "approve_confidence_low"
    assert signal.category == "risk"
    assert signal.score == 3
    assert signal.reason == "approve decision with low confidence"
    assert signal.evidence == {
        "decision_type": "approve",
        "confidence": 0.3
    }
    assert signal.is_critical_override is False
    assert signal.metadata == {}


def test_latency_high_signal():
    event = DecisionEvent(
        event_id = "evt_signal_003",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "latency_high"
    assert signal.category == "risk"
    assert signal.score == 2
    assert signal.reason == "response latency exceeded threshold"
    assert signal.evidence == {
        "latency_ms": 2800
    }
    assert signal.is_critical_override is False
    assert signal.metadata == {}

def test_missing_confidence_signal():
    event = DecisionEvent(
        event_id = "evt_signal_004",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "missing_confidence"
    assert signal.category == "uncertainty"
    assert signal.score == 1
    assert signal.reason == "confidence field is missing"
    assert signal.evidence == {
        "confidence": None
    }
    assert signal.is_critical_override is False
    assert signal.metadata == {}

def test_missing_model_version_signal_when_none():
    event = DecisionEvent(
        event_id = "evt_signal_005",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "missing_model_version"
    assert signal.category == "uncertainty"
    assert signal.score == 1
    assert signal.reason == "model_version field is missing"
    assert signal.evidence == {
        "model_version": None
    }
    assert signal.is_critical_override is False
    assert signal.metadata == {}

def test_missing_model_version_signal_when_blank():
    event = DecisionEvent(
        event_id = "evt_signal_006",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "   ",
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "missing_model_version"
    assert signal.category == "uncertainty"
    assert signal.score == 1
    assert signal.evidence == {
        "model_version": None
    }

def test_evaluation_integrity_override_signal():
    event = DecisionEvent(
        event_id = "evt_signal_007",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert len(signals) == 1

    signal = signals[0]

    assert signal.rule_id == "evaluation_integrity_override"
    assert signal.category == "failure"
    assert signal.score == 0
    assert signal.reason == "evaluation integrity failure requires critical review"
    assert signal.evidence == {
        "error_code": "gateway_failure"
    }
    assert signal.is_critical_override is True
    assert signal.metadata == {
        "failure_type": "system_error",
        "score_contribution": "none",
        "override_type": "critical"
    }

def test_multiple_triggered_rules_create_multiple_signals():
    event = DecisionEvent(
        event_id = "evt_signal_008",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = None,
        error_code = None
    )

    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)

    assert [signal.rule_id for signal in signals] == [
        "approve_confidence_low",
        "latency_high",
        "missing_model_version"
    ]