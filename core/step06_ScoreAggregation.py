from dataclasses import dataclass
from .step05_SignalGeneration import Signal

@dataclass(frozen=True)
class SignalSummary:
    risk_score: int
    uncertainty_score: int
    has_critical_override_signal: bool
    has_stability_signal: bool

def summarize_signals(signals: list[Signal]) -> SignalSummary:
    risk_score = sum(
        signal.score for signal in signals if signal.category == "risk"
    )
    uncertainty_score = sum(
        signal.score for signal in signals if signal.category == "uncertainty"
    )
    has_critical_override_signal = any(
        signal.is_critical_override for signal in signals
    )
    has_stability_signal = any(
        signal.category == "stability" for signal in signals
    )
    return SignalSummary(
        risk_score = risk_score,
        uncertainty_score = uncertainty_score,
        has_critical_override_signal = has_critical_override_signal,
        has_stability_signal = has_stability_signal
    )