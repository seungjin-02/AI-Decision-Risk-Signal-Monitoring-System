from core.step05_SignalGeneration import Signal
from core.step06_ScoreAggregation import summarize_signals


def test_summarize_risk_score():
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

    summary = summarize_signals(signals)

    assert summary.risk_score == 5
    assert summary.uncertainty_score == 0
    assert summary.has_critical_override_signal is False
    assert summary.has_stability_signal is False


def test_summarize_uncertainty_score():
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

    summary = summarize_signals(signals)

    assert summary.risk_score == 0
    assert summary.uncertainty_score == 2
    assert summary.has_critical_override_signal is False
    assert summary.has_stability_signal is False


def test_summarize_risk_and_uncertainty_scores():
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

    summary = summarize_signals(signals)

    assert summary.risk_score == 5
    assert summary.uncertainty_score == 2
    assert summary.has_critical_override_signal is False
    assert summary.has_stability_signal is False


def test_failure_signal_critical_override():
    signals = [
        Signal(
            rule_id = "evaluation_integrity_override",
            category = "failure",
            score = 0,
            reason = "evaluation integrity failure requires critical review",
            is_critical_override = True,
            metadata = {
                "failure_type": "system_error",
                "score_contribution": "none",
                "override_type": "critical"
            }
        )
    ]

    summary = summarize_signals(signals)

    assert summary.risk_score == 0
    assert summary.uncertainty_score == 0
    assert summary.has_critical_override_signal is True
    assert summary.has_stability_signal is False


def test_stability_signal_sets_stability_flag_without_changing_scores():
    signals = [
        Signal(
            rule_id = "stability_signal",
            category = "stability",
            score = 0,
            reason = "stability signal detected"
        )
    ]

    summary = summarize_signals(signals)

    assert summary.risk_score == 0
    assert summary.uncertainty_score == 0
    assert summary.has_critical_override_signal is False
    assert summary.has_stability_signal is True


def test_empty_signals_summary():
    signals = []

    summary = summarize_signals(signals)

    assert summary.risk_score == 0
    assert summary.uncertainty_score == 0
    assert summary.has_critical_override_signal is False
    assert summary.has_stability_signal is False