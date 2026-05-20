from dataclasses import dataclass
from enum import Enum
from step06_ScoreAggregation import GateInputs

class RiskLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class DecisionBoundaryResult:
    """
    자동화 허용 경계만 표현한다.

    boundary는 위험 수준 자체를 설명하는 객체가 아니라,
    현재 해석 결과를 시스템이 자동으로 확정해도 되는지 여부를 나타낸다.
    """
    auto_finalize_allowed: bool
    reason: str

@dataclass(frozen=True)
class HumanReviewRequirement:
    """
    인간 검토 필요 여부를 표현한다.

    human_required는 위험 수준(final_level)과 별개 차원이며,
    시스템이 현재 판단을 스스로 확정할 수 있는지와 관련된다.
    """
    required: bool
    reason: str
    source: str = "decision_boundary"

@dataclass(frozen=True)
class GateDecision:
    final_level: RiskLevel
    boundary: DecisionBoundaryResult
    human_review: HumanReviewRequirement
    gate_reason: str

def interpret_gate(inputs: GateInputs) -> GateDecision:
    low_uncertainty = inputs.uncertainty_score == 0
    high_uncertainty = inputs.uncertainty_score >= 1

    # Rule1. High risk override
    if inputs.has_high_risk_signal:
        final_level = RiskLevel.CRITICAL
        human_required = True
        gate_reason = (
            "high-risk signal triggered critical interpretation and requires human review"
        )

    # Rule2. High risk zone
    elif inputs.risk_score >= 4:
        if low_uncertainty:
            final_level = RiskLevel.CRITICAL
            human_required = True
            gate_reason = (
                "high risk score with low uncertainty allows critical escalation"
            )
        else:
            final_level = RiskLevel.WARN
            human_required = True
            gate_reason = (
                "high risk score detected, but uncertainty prevents automatic critical finalization"
            )

    # Rule3. Medium risk zone
    elif inputs.risk_score >= 2:
        if high_uncertainty:
            final_level = RiskLevel.WARN
            human_required = True
            gate_reason = (
                "medium risk with uncertainty requires human review before final interpretation"
            )
        else:
            final_level = RiskLevel.WARN
            human_required = False
            gate_reason = (
                "medium risk with low uncertainty can be handled as warning-level interpretation"
            )

    # Rule4. Low risk zone
    else:
        if high_uncertainty:
            final_level = RiskLevel.INFO
            human_required = False
            gate_reason = (
                "risk remains low, while uncertainty is present; action-level caution is recommended"
            )
        else:
            final_level = RiskLevel.INFO
            human_required = False
            gate_reason = (
                "risk signals remain low and do not require escalation"
            )

    # Rule5. Stability mitigation (현재 구현 상태에서는 극히 제한적으로 조건만 명시)
    if (inputs.has_stability_signal and final_level == RiskLevel.WARN and inputs.risk_score <= 2 and low_uncertainty):
        final_level = RiskLevel.INFO
        human_required = False
        gate_reason = (
            "stability signal mitigated warning interpretation in a low-risk, low-uncertainty context"
        )

    boundary = DecisionBoundaryResult(
        auto_finalize_allowed = not human_required,
        reason = (
            "automatic finalization is restricted" if human_required
            else "automatic finalization is allowed"
        )
    )

    human_review = HumanReviewRequirement(
        required = human_required,
        reason = (
            "human review is required" if human_required
            else "human review is not required"
        )
    )

    return GateDecision(
        final_level = final_level,
        boundary = boundary,
        human_review = human_review,
        gate_reason = gate_reason
    )



