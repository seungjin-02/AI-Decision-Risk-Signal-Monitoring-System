from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context
from core.step04_RuleEvaluation import evaluate_rule
from core.step05_SignalGeneration import build_signals
from core.step06_ScoreAggregation import aggregate_scores, derive_gate_inputs
from core.step07_GateInterpretation import interpret_gate, RiskLevel
from core.step08_ActionGeneration import generate_action
from core.step09_AlertOutput import build_alert_output

def run_pipeline_until_alert(event: DecisionEvent):
    normalized = normalize_event(event)
    context = build_evaluation_context(event)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)
    score_summary = aggregate_scores(signals)
    gate_inputs = derive_gate_inputs(signals, score_summary)
    decision = interpret_gate(gate_inputs)
    action = generate_action(decision, signals)
    alert = build_alert_output(
        event = normalized,
        signals = signals,
        signal_summary= score_summary,
        decision = decision,
        action = action
    )

    return {
        "normalized": normalized,
        "context": context,
        "evaluations": evaluations,
        "signals": signals,
        "score_summary": score_summary,
        "gate_inputs": gate_inputs,
        "decision": decision,
        "action": action,
        "alert": alert,
    }

def test_uncertainty_signal_does_not_increase_risk_score():
    event = DecisionEvent(
        event_id = "event001",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = None,
        error_code= None
    )

    result = run_pipeline_until_alert(event)
    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 2
    assert result["alert"].level == "INFO"

def test_high_risk_signal_override():
    event = DecisionEvent(
        event_id = "event002",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    result = run_pipeline_until_alert(event)
    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 0
    assert result["gate_inputs"].has_high_risk_signal is True
    assert result["decision"].final_level == RiskLevel.CRITICAL
    assert result["alert"].human_required is True

def test_high_risk_with_uncertainty():
    event = DecisionEvent(
        event_id = "event003",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = None,
        error_code = None
    )

    result = run_pipeline_until_alert(event)
    assert result["alert"].risk_score == 5
    assert result["alert"].uncertainty_score == 1
    assert result["alert"].level == "WARN"
    assert result["alert"].human_required is True
    assert result["decision"].boundary.auto_finalize_allowed is False

def test_low_risk_with_uncertainty():
    event = DecisionEvent(
        event_id = "event004",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    result = run_pipeline_until_alert(event)
    assert result["alert"].risk_score == 0
    assert result["alert"].uncertainty_score == 1
    assert result["alert"].level == "INFO"
    assert result["alert"].human_required is False
    assert "review_missing_or_incomplete_information" in result["alert"].recommended_actions

def test_alert_output_results():
    event = DecisionEvent(
        event_id = "event005",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = None,
        error_code = None
    )

    result = run_pipeline_until_alert(event)
    assert result["alert"].event_id == result["normalized"].event_id
    assert result["alert"].risk_score == result["score_summary"].risk_score
    assert result["alert"].uncertainty_score == result["score_summary"].uncertainty_score
    assert result["alert"].level == result["decision"].final_level.value
    assert result["alert"].human_required == result["decision"].human_review.required
    assert result["alert"].recommended_actions == result["action"].actions


























