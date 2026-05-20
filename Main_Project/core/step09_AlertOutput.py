from dataclasses import dataclass, field
from typing import Any
from step02_NormalizedEvent import NormalizedEvent
from step05_SignalGeneration import Signal
from step06_ScoreAggregation import ScoreSummary
from step07_GateInterpretation import GateDecision
from step08_ActionGeneration import ActionRecommendation


@dataclass(frozen=True)
class AlertOutput:
    event_id: str
    level: str
    risk_score: int
    uncertainty_score: int
    human_required: bool
    recommended_actions: list[str]
    reason_summary: str
    signals: list[Signal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

def build_alert_output(
    event: NormalizedEvent,
    signals: list[Signal],
    score_summary: ScoreSummary,
    decision: GateDecision,
    action: ActionRecommendation
) -> AlertOutput:
    return AlertOutput(
        event_id = event.event_id,
        level = decision.final_level.value,
        risk_score = score_summary.risk_score,
        uncertainty_score = score_summary.uncertainty_score,
        human_required = decision.human_review.required,
        recommended_actions = action.actions,
        reason_summary=action.message,
        signals = signals,
        metadata = dict(event.metadata)
    )