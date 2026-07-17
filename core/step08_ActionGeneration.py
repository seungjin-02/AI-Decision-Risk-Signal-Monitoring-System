from dataclasses import dataclass
from .step05_SignalGeneration import Signal
from .step07_GateInterpretation import GateDecision, RiskLevel

@dataclass(frozen=True)
class ActionRecommendation:
    actions: list[str]
    message: str

def generate_action(
    decision: GateDecision,
    signals: list[Signal]
) -> ActionRecommendation:
    actions : list[str] = []

    # 1. human_required 기반 (인간의 개입을 가장 우선시)
    if decision.human_review.required:
        actions.append("human_review_required") # 책임 전이와 운영 대응을 분리

    # 2. critical override 기반
    if any(signal.is_critical_override for signal in signals):
        actions.append("immediate_investigation")

    # 3. uncertainty 기반
    uncertainty_present = any(
        signal.category == "uncertainty" for signal in signals
    )
    if uncertainty_present:
        actions.append("review_missing_or_incomplete_information")

    # 4. risk 기반
    if decision.final_level == RiskLevel.CRITICAL:
        actions.append("escalate_incident")
    elif decision.final_level == RiskLevel.WARN:
        actions.append("monitor_closely")
    else:
        actions.append("no_immediate_action_required")

    # message 생성
    message = decision.gate_reason
    return ActionRecommendation(actions, message)



