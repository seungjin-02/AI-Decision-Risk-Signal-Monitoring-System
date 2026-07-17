from core.step06_ScoreAggregation import SignalSummary
from core.step07_GateInterpretation import interpret_gate, RiskLevel

def make_signal_summary(
    risk_score: int,
    uncertainty_score: int,
    has_critical_override_signal: bool = False,
    has_stability_signal: bool = False
) -> SignalSummary:
    return SignalSummary(
        risk_score = risk_score,
        uncertainty_score = uncertainty_score,
        has_critical_override_signal = has_critical_override_signal,
        has_stability_signal = has_stability_signal
    )


def test_low_risk_low_uncertainty():
    inputs = make_signal_summary(
        risk_score = 0,
        uncertainty_score = 0
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_low_risk_with_uncertainty():
    inputs = make_signal_summary(
        risk_score=0,
        uncertainty_score=1,
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_medium_risk_low_uncertainty():
    inputs = make_signal_summary(
        risk_score = 2,
        uncertainty_score = 0
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True


def test_medium_risk_with_uncertainty():
    inputs = make_signal_summary(
        risk_score = 2,
        uncertainty_score = 1
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False


def test_high_risk_low_uncertainty():
    inputs = make_signal_summary(
        risk_score = 5,
        uncertainty_score = 0
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False


def test_high_risk_with_uncertainty():
    inputs = make_signal_summary(
        risk_score = 5,
        uncertainty_score = 1
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False


def test_critical_override_signal_overrides_low_risk_low_uncertainty():
    inputs = make_signal_summary(
        risk_score = 0,
        uncertainty_score = 0,
        has_critical_override_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False


def test_critical_override_signal_overrides_low_risk_with_uncertainty():
    inputs = make_signal_summary(
        risk_score = 0,
        uncertainty_score = 1,
        has_critical_override_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_stability_signal_warn_to_info():
    inputs = make_signal_summary(
        risk_score = 2,
        uncertainty_score = 0,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True


def test_stability_signal_does_not_mitigate_critical_level():
    inputs = make_signal_summary(
        risk_score = 5,
        uncertainty_score = 0,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False


def test_stability_signal_does_not_mitigate_when_uncertainty_exists():
    inputs = make_signal_summary(
        risk_score = 2,
        uncertainty_score = 1,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False