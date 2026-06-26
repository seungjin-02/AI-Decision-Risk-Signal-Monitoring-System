from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context
from core.step04_RuleEvaluation import evaluate_rule
from core.step05_SignalGeneration import build_signals

def build_signals_from_event(event: DecisionEvent):
    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    return build_signals(evaluations, normalized)

def get_signal_by_rule_id(signals, rule_id: str):
    for signal in signals:
        if signal.rule_id == rule_id:
            return signal
    return None

def test_no_signal_when_no_triggered():
    event = DecisionEvent(
        event_id = "event_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    signals = build_signals_from_event(event)
    assert signals == []

def test_low_confidence():
    event = DecisionEvent(
        event_id = "event_002",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    signals = build_signals_from_event(event)
    signal = get_signal_by_rule_id(signals, "approve_confidence_low")
    assert signal is not None
    assert signal.category == "risk"
    assert signal.score == 3
    assert signal.is_high_risk is False

def test_latency_high():
    event = DecisionEvent(
        event_id = "event_003",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    signals = build_signals_from_event(event)
    signal = get_signal_by_rule_id(signals, "latency_high")

    assert signal is not None
    assert signal.category == "risk"
    assert signal.score == 2
    assert signal.is_high_risk is False

def test_missing_confidence():
    event = DecisionEvent(
        event_id = "event_004",
        decision_type = "approve",
        confidence = None,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    signals = build_signals_from_event(event)
    signal = get_signal_by_rule_id(signals, "missing_confidence")
    assert signal is not None
    assert signal.category == "uncertainty"
    assert signal.score == 1
    assert signal.is_high_risk is False

def test_missing_model_version():
    event = DecisionEvent(
        event_id = "event_005",
        decision_type = "approve",
        confidence = None,
        latency_ms = 2800,
        model_version = None,
        error_code = None
    )

    signals = build_signals_from_event(event)
    signal = get_signal_by_rule_id(signals, "missing_model_version")
    assert signal is not None
    assert signal.category == "uncertainty"
    assert signal.score == 1
    assert signal.is_high_risk is False

def test_is_high_risk_override():
    event = DecisionEvent(
        event_id = "event_006",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    signals = build_signals_from_event(event)
    signal = get_signal_by_rule_id(signals, "system_error_override")
    assert signal is not None
    assert signal.category == "risk"
    assert signal.score == 0
    assert signal.is_high_risk is True




































