from dataclasses import dataclass
from step05_SignalGeneration import Signal

@dataclass(frozen=True)
class ScoreSummary:
    risk_score: int
    uncertainty_score: int

@dataclass(frozen=True)
class GateInputs:
    risk_score: int
    uncertainty_score: int
    has_high_risk_signal: bool
    has_stability_signal: bool

def aggregate_scores(signals: list[Signal]) -> ScoreSummary:
    risk_score = sum(
        signal.score for signal in signals if signal.category == "risk"
    )
    uncertainty_score = sum(
        signal.score for signal in signals if signal.category == "uncertainty"
    )
    return ScoreSummary(
        risk_score = risk_score,
        uncertainty_score = uncertainty_score,
    )

def derive_gate_inputs(
    signals: list[Signal],
    score_summary: ScoreSummary
) -> GateInputs:
    has_high_risk_signal = any(
        signal.is_high_risk for signal in signals
    )
    has_stability_signal = any(
        signal.category == "stability" for signal in signals
    )

    return GateInputs(
        risk_score = score_summary.risk_score,
        uncertainty_score = score_summary.uncertainty_score,
        has_high_risk_signal = has_high_risk_signal,
        has_stability_signal = has_stability_signal
    )