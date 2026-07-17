from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context
from core.step04_RuleEvaluation import evaluate_rule
from core.step05_SignalGeneration import build_signals
from core.step06_ScoreAggregation import summarize_signals
from core.step07_GateInterpretation import interpret_gate, RiskLevel
from core.step08_ActionGeneration import generate_action
from core.step09_AlertOutput import build_alert_output

def run_pipeline_until_alert(event: DecisionEvent):
    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)
    signal_summary = summarize_signals(signals)
    decision = interpret_gate(signal_summary)
    action = generate_action(decision, signals)
    alert = build_alert_output(
        event=normalized,
        signals=signals,
        signal_summary=signal_summary,
        decision=decision,
        action=action
    )

    return {
        "normalized": normalized,
        "context": context,
        "evaluations": evaluations,
        "signals": signals,
        "signal_summary": signal_summary,
        "decision": decision,
        "action": action,
        "alert": alert
    }

def test_uncertainty_signal():
    event = DecisionEvent(
        event_id="event001",
        decision_type="approve",
        confidence=None,
        latency_ms=800,
        model_version=None,
        error_code=None
    )

    result = run_pipeline_until_alert(event)

    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 2
    assert result["alert"].level == "INFO"

def test_critical_override_signal():
    event = DecisionEvent(
        event_id="event002",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version="v1",
        error_code="gateway_failure"
    )

    result = run_pipeline_until_alert(event)

    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 0
    assert result["signal_summary"].has_critical_override_signal is True
    assert result["decision"].final_level == RiskLevel.CRITICAL
    assert result["alert"].level == "CRITICAL"
    assert result["alert"].human_required is True

    override_signals = [
        signal
        for signal in result["signals"]
        if signal.rule_id == "evaluation_integrity_override"
    ]

    assert len(override_signals) == 1
    assert override_signals[0].category == "failure"
    assert override_signals[0].score == 0
    assert override_signals[0].is_critical_override is True


def test_high_risk_with_uncertainty():
    event = DecisionEvent(
        event_id="event003",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version=None,
        error_code=None,
    )

    result = run_pipeline_until_alert(event)

    assert result["alert"].risk_score == 5
    assert result["alert"].uncertainty_score == 1
    assert result["alert"].level == "WARN"
    assert result["alert"].human_required is True
    assert result["decision"].boundary.auto_finalize_allowed is False


def test_low_risk_with_uncertainty():
    event = DecisionEvent(
        event_id="event004",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version=None,
        error_code=None,
    )

    result = run_pipeline_until_alert(event)

    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 1
    assert result["alert"].level == "INFO"
    assert result["alert"].human_required is False
    assert "review_missing_or_incomplete_information" in result["alert"].recommended_actions


def test_alert_output():
    event = DecisionEvent(
        event_id="event005",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version=None,
        error_code=None,
    )

    result = run_pipeline_until_alert(event)

    assert result["alert"].event_id == result["normalized"].event_id
    assert result["alert"].risk_score == result["signal_summary"].risk_score
    assert result["alert"].uncertainty_score == result["signal_summary"].uncertainty_score
    assert result["alert"].level == result["decision"].final_level.value
    assert result["alert"].human_required == result["decision"].human_review.required
    assert result["alert"].recommended_actions == result["action"].actions