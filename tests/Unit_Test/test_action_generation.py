from core.step05_SignalGeneration import Signal
from core.step07_GateInterpretation import RiskLevel, DecisionBoundaryResult, HumanReviewRequirement, GateDecision
from core.step08_ActionGeneration import generate_action

def test_human_required_adds_human_review_action():
    decision = GateDecision(
        final_level = RiskLevel.WARN,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = False,
            reason = "automatic finalization is restricted"
        ),
        human_review = HumanReviewRequirement(
            required = True,
            reason = "human review is required"
        ),
        gate_reason = "test gate reason"
    )

    signals = []

    action = generate_action(decision, signals)

    assert action.actions == [
        "human_review_required",
        "monitor_closely"
    ]

def test_critical_override_adds_immediate_investigation():
    decision = GateDecision(
        final_level = RiskLevel.CRITICAL,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = False,
            reason = "automatic finalization is restricted"
        ),
        human_review = HumanReviewRequirement(
            required = True,
            reason = "human review is required"
        ),
        gate_reason = "test gate reason"
    )

    signals = [
        Signal(
            rule_id = "evaluation_integrity_override",
            category = "failure",
            score = 0,
            reason = "evaluation integrity failure requires critical review",
            is_critical_override = True
        )
    ]

    action = generate_action(decision, signals)

    assert action.actions == [
        "human_review_required",
        "immediate_investigation",
        "escalate_incident",
    ]


def test_uncertainty_signal_adds_missing_information_review_action():
    decision = GateDecision(
        final_level = RiskLevel.INFO,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = True,
            reason = "automatic finalization is allowed"
        ),
        human_review = HumanReviewRequirement(
            required = False,
            reason = "human review is not required"
        ),
        gate_reason = "test gate reason"
    )

    signals = [
        Signal(
            rule_id = "missing_model_version",
            category = "uncertainty",
            score = 1,
            reason = "model_version field is missing",
            is_critical_override = False
        )
    ]

    action = generate_action(decision, signals)

    assert action.actions == [
        "review_missing_or_incomplete_information",
        "no_immediate_action_required"
    ]

def test_human_required_with_uncertainty_and_warn_level_action_order():
    decision = GateDecision(
        final_level = RiskLevel.WARN,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = False,
            reason = "automatic finalization is restricted"
        ),
        human_review = HumanReviewRequirement(
            required = True,
            reason = "human review is required"
        ),
        gate_reason = "test gate reason"
    )

    signals = [
        Signal(
            rule_id = "missing_confidence",
            category = "uncertainty",
            score = 1,
            reason = "confidence field is missing",
            is_critical_override = False
        )
    ]

    action = generate_action(decision, signals)

    assert action.actions == [
        "human_review_required",
        "review_missing_or_incomplete_information",
        "monitor_closely"
    ]

def test_warn_level_adds_monitor_closely():
    decision = GateDecision(
        final_level = RiskLevel.WARN,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = True,
            reason = "automatic finalization is allowed"
        ),
        human_review = HumanReviewRequirement(
            required = False,
            reason = "human review is not required"
        ),
        gate_reason = "test gate reason"
    )

    signals = []

    action = generate_action(decision, signals)

    assert action.actions == [
        "monitor_closely"
    ]

def test_info_level_adds_no_immediate_action_required():
    decision = GateDecision(
        final_level = RiskLevel.INFO,
        boundary = DecisionBoundaryResult(
            auto_finalize_allowed = True,
            reason = "automatic finalization is allowed"
        ),
        human_review = HumanReviewRequirement(
            required = False,
            reason = "human review is not required"
        ),
        gate_reason = "test gate reason"
    )

    signals = []

    action = generate_action(decision, signals)

    assert action.actions == [
        "no_immediate_action_required"
    ]