from core.step05_SignalGeneration import Signal
from core.step06_ScoreAggregation import aggregate_scores, derive_gate_inputs

def test_aggregate_risk_score():
    signals = [
        Signal(
            rule_id = "approve_confidence_low",
            category = "risk",
            score = 3,
            reason = "approve decision with low confidence"
        ),
        Signal(
            rule_id = "latency_high",
            category = "risk",
            score = 2,
            reason = "response latency exceeded threshold"
        )
    ]

    score_summary = aggregate_scores(signals)
    assert score_summary.risk_score == 5
    assert score_summary.uncertainty_score == 0

def test_aggregate_uncertainty_score():
    signals = [
        Signal(
            rule_id = "missing_confidence",
            category = "uncertainty",
            score = 1,
            reason = "confidence field is missing"
        ),
        Signal(
            rule_id = "missing_model_version",
            category = "uncertainty",
            score = 1,
            reason = "model_version field is missing"
        )
    ]

    score_summary = aggregate_scores(signals)
    assert score_summary.risk_score == 0
    assert score_summary.uncertainty_score == 2

def test_aggregate_risk_uncertainty_score():
    signals = [
        Signal(
            rule_id = "approve_confidence_low",
            category = "risk",
            score = 3,
            reason = "approve decision with low confidence"
        ),
        Signal(
            rule_id = "latency_high",
            category = "risk",
            score = 2,
            reason = "response latency exceeded threshold"
        ),
        Signal(
            rule_id = "missing_confidence",
            category = "uncertainty",
            score = 1,
            reason = "confidence field is missing"
        ),
        Signal(
            rule_id = "missing_model_version",
            category = "uncertainty",
            score = 1,
            reason = "model_version field is missing"
        )
    ]

    score_summary = aggregate_scores(signals)
    assert score_summary.risk_score == 5
    assert score_summary.uncertainty_score == 2

def test_aggregate_high_risk():
    signals = [
        Signal(
            rule_id = "system_error_override",
            category = "risk",
            score = 0,
            reason="approve decision with low confidence",
            is_high_risk = True
        )
    ]

    score_summary = aggregate_scores(signals)
    gate_inputs = derive_gate_inputs(signals, score_summary)
    assert score_summary.risk_score == 0
    assert score_summary.uncertainty_score == 0
    assert gate_inputs.has_high_risk_signal is True
    assert gate_inputs.has_stability_signal is False

def test_aggregate_stability():
    signals = [
        Signal(
            rule_id = "stable-context",
            category = "stability",
            score = 0,
            reason = "stable context detected"
        )
    ]

    score_summary = aggregate_scores(signals)
    gate_inputs = derive_gate_inputs(signals, score_summary)
    assert score_summary.risk_score == 0
    assert score_summary.uncertainty_score == 0
    assert gate_inputs.has_high_risk_signal is False
    assert gate_inputs.has_stability_signal is True
