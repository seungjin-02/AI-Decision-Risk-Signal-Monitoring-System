from dataclasses import asdict
import json

from .event_validation import validate_event, format_validation_issues
from .step01_DecisionEvent import DecisionEvent
from .step02_NormalizedEvent import normalize_event
from .step03_EvaluationContext import build_evaluation_context
from .step04_RuleEvaluation import evaluate_rule
from .step05_SignalGeneration import build_signals
from .step06_ScoreAggregation import summarize_signals
from .step07_GateInterpretation import interpret_gate
from .step08_ActionGeneration import generate_action
from .step09_AlertOutput import build_alert_output, AlertOutput

def evaluate_event(event: DecisionEvent) -> AlertOutput:
    validation = validate_event(event)
    if not validation.is_valid:
        raise ValueError(format_validation_issues(validation.issues))
    normalized = normalize_event(event)
    context = build_evaluation_context(normalized)
    evaluations = evaluate_rule(normalized, context)
    signals = build_signals(evaluations, normalized)
    signal_summary = summarize_signals(signals)
    decision = interpret_gate(signal_summary)
    action = generate_action(decision, signals)

    return build_alert_output(
        event = normalized,
        signals = signals,
        signal_summary = signal_summary,
        decision = decision,
        action = action
    )

def print_alert(alert: AlertOutput) -> None:
    print(json.dumps(asdict(alert), indent = 2, ensure_ascii = False))

if __name__ == "__main__":
    event = DecisionEvent(
        event_id="evt_timeout_001",
        decision_type="approve",
        confidence=0.9,
        latency_ms=100,
        model_version="v1",
        error_code="timeout_01"
    )

    alert = evaluate_event(event)
    print_alert(alert)