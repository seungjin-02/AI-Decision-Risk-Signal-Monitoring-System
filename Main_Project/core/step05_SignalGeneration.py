from dataclasses import dataclass, field
from typing import Any

from step02_NormalizedEvent import NormalizedEvent
from step04_RuleEvaluation import RuleEvaluation

@dataclass(frozen=True)
class Signal:
    rule_id: str
    category: str
    score: int
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)
    is_high_risk: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

def _build_evidence(
    event: NormalizedEvent,
    evidence_fields: list[str]
) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for field_name in evidence_fields:
        evidence[field_name] = getattr(event, field_name, None)
    return evidence

def build_signals(
    evaluations: list[RuleEvaluation],
    event: NormalizedEvent
) -> list[Signal]:
    signals: list[Signal] = []
    for evaluation in evaluations:
        if not evaluation.triggered:
            continue
        rule = evaluation.rule
        signal = Signal(
            rule_id = rule.rule_id,
            category = rule.category,
            score = rule.score,
            reason = rule.reason,
            evidence = _build_evidence(event, rule.evidence_fields),
            is_high_risk = rule.is_high_risk,
            metadata = dict(rule.metadata),
        )
        signals.append(signal)
    return signals