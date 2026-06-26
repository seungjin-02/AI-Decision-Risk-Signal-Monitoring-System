from core.step05_SignalGeneration import Signal
from core.step07_GateInterpretation import (
    RiskLevel,
    DecisionBoundaryResult,
    HumanReviewRequirement,
    GateDecision,
)
from core.step08_ActionGeneration import generate_action

def make_gate_decision(
    level: RiskLevel,
    human_required: bool,
    auto_finalize_allowed: bool,
    gate_reason: str = "test gate reason"
) -> GateDecision:
    boundary = DecisionBoundaryResult(
        auto_finalize_allowed = auto_finalize_allowed,
        reason = (
            "automatic finalization is restricted" if not auto_finalize_allowed
            else "automatic finalization is allowed"
        )
    )

    human_review = HumanReviewRequirement(
        required = human_required,
        reason = (
            "human review is restricted" if human_required
            else "human review is allowed"
        )
    )

    return GateDecision(
        final_level = level,
        boundary = boundary,
        human_review = human_review,
        gate_reason = gate_reason
    )

def test_human_required():
    decision = make_gate_decision(
        level = RiskLevel.WARN,
        human_required = True,
        auto_finalize_allowed = False
    )

    signals = []
    action = generate_action(decision, signals)
    assert "human_review_required" in action.actions

def test_high_risk_signal_override():
    decision = make_gate_decision(
        level = RiskLevel.CRITICAL,
        human_required = True,
        auto_finalize_allowed = False
    )

    signals = [
        Signal(
            rule_id = "system_error_override",
            category = "risk",
            score = 0,
            reason = "system error detected",
            is_high_risk = True
        )
    ]

    action = generate_action(decision, signals)
    assert "immediate_investigation" in action.actions

def test_uncertainty_signal_missing_information():
    decision = make_gate_decision(
        level = RiskLevel.INFO,
        human_required = False,
        auto_finalize_allowed = True
    )

    signals = [
        Signal(
            rule_id = "missing_model_version",
            category = "uncertainty",
            score = 1,
            reason = "model version missing",
            is_high_risk = False,
        )
    ]
    action = generate_action(decision, signals)
    assert "review_missing_or_incomplete_information" in action.actions

def test_uncertainty_human_review_required():
    decision = make_gate_decision(
        level = RiskLevel.WARN,
        human_required = True,
        auto_finalize_allowed = False
    )

    signals = [
        Signal(
            rule_id = "missing_confidence",
            category = "uncertainty",
            score = 1,
            reason = "system error detected",
            is_high_risk = False
        )
    ]
    action = generate_action(decision, signals)
    assert "human_review_required" in action.actions
    assert "review_missing_or_incomplete_information" in action.actions

def test_critical_level():
    decision = make_gate_decision(
        level = RiskLevel.CRITICAL,
        human_required = True,
        auto_finalize_allowed = False
    )

    signals = []
    action = generate_action(decision, signals)
    assert "escalate_incident" in action.actions

def test_warn_level():
    decision = make_gate_decision(
        level = RiskLevel.WARN,
        human_required = False,
        auto_finalize_allowed = True
    )

    signals = []
    action = generate_action(decision, signals)
    assert "monitor_closely" in action.actions

def test_info_level():
    decision = make_gate_decision(
        level = RiskLevel.INFO,
        human_required = False,
        auto_finalize_allowed = True
    )

    signals = []
    action = generate_action(decision, signals)
    assert "no_immediate_action_required" in action.actions

def test_action_generation():
    decision = make_gate_decision(
        level = RiskLevel.WARN,
        human_required = True,
        auto_finalize_allowed = False,
        gate_reason = "medium risk with uncertainty requires human review before final interpretation",
    )

    signals = [
        Signal(
            rule_id = "missing_confidence",
            category = "uncertainty",
            score = 1,
            reason = "confidence missing",
            is_high_risk = False
        )
    ]

    action = generate_action(decision, signals)
    assert decision.final_level == RiskLevel.WARN
    assert decision.human_review.required is True
    assert decision.boundary.auto_finalize_allowed is False
    assert decision.gate_reason == (
        "medium risk with uncertainty requires human review before final interpretation"
    )
    assert "human_review_required" in action.actions
    assert "review_missing_or_incomplete_information" in action.actions
    assert action.message == decision.gate_reason









