from core.step06_ScoreAggregation import GateInputs
from core.step07_GateInterpretation import interpret_gate, RiskLevel

def make_gate_inputs(
        risk_score: int,
        uncertainty_score: int,
        has_high_risk_signal: bool = False,
        has_stability_signal: bool = False
) -> GateInputs:
    return GateInputs(
        risk_score = risk_score,
        uncertainty_score = uncertainty_score,
        has_high_risk_signal = has_high_risk_signal,
        has_stability_signal = has_stability_signal
    )

def test_low_risk_low_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 0,
        uncertainty_score = 0,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_medium_risk_low_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 2,
        uncertainty_score = 0,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_medium_risk_with_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 2,
        uncertainty_score = 1,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_high_risk_low_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 5,
        uncertainty_score = 0,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_high_risk_with_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 5,
        uncertainty_score = 1,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_high_risk_signal_overrides_low_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 0,
        uncertainty_score = 0,
        has_high_risk_signal = True,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_high_risk_signal_overrides_with_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 0,
        uncertainty_score = 1,
        has_high_risk_signal = True,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_low_risk_with_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 0,
        uncertainty_score = 1,
        has_high_risk_signal = False,
        has_stability_signal = False
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_stability_signal_warn_to_info():
    inputs = make_gate_inputs(
        risk_score = 2,
        uncertainty_score = 0,
        has_high_risk_signal = False,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.INFO
    assert decision.human_review.required is False
    assert decision.boundary.auto_finalize_allowed is True

def test_stability_signal_with_critical():
    inputs = make_gate_inputs(
        risk_score = 5,
        uncertainty_score = 0,
        has_high_risk_signal = False,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.CRITICAL
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False

def test_stability_signal_with_uncertainty():
    inputs = make_gate_inputs(
        risk_score = 2,
        uncertainty_score = 1,
        has_high_risk_signal = False,
        has_stability_signal = True
    )

    decision = interpret_gate(inputs)

    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False