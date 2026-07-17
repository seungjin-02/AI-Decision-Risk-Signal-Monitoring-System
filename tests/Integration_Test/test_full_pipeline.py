import pytest
from core.step01_DecisionEvent import DecisionEvent
from core.main import evaluate_event

def test_normal_case_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.event_id == "event_pipeline_001"
    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 0
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "no_immediate_action_required"
    ]
    assert alert.signals == []

def test_low_confidence_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_002",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "WARN"
    assert alert.risk_score == 3
    assert alert.uncertainty_score == 0
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "monitor_closely"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "approve_confidence_low"
    ]

def test_high_latency_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_003",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "WARN"
    assert alert.risk_score == 2
    assert alert.uncertainty_score == 0
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "monitor_closely"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "latency_high"
    ]

def test_high_risk_without_uncertainty_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_004",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "CRITICAL"
    assert alert.risk_score == 5
    assert alert.uncertainty_score == 0
    assert alert.human_required is True
    assert alert.recommended_actions == [
        "human_review_required",
        "escalate_incident"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "approve_confidence_low",
        "latency_high"
    ]

def test_high_risk_with_uncertainty_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_005",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = "   ",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "WARN"
    assert alert.risk_score == 5
    assert alert.uncertainty_score == 1
    assert alert.human_required is True
    assert alert.recommended_actions == [
        "human_review_required",
        "review_missing_or_incomplete_information",
        "monitor_closely"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "approve_confidence_low",
        "latency_high",
        "missing_model_version"
    ]

def test_evaluation_integrity_override_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_006",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    alert = evaluate_event(event)

    assert alert.level == "CRITICAL"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 0
    assert alert.human_required is True
    assert alert.recommended_actions == [
        "human_review_required",
        "immediate_investigation",
        "escalate_incident"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "evaluation_integrity_override"
    ]
    assert alert.signals[0].category == "failure"

def test_missing_confidence_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_007",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 1
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "review_missing_or_incomplete_information",
        "no_immediate_action_required"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "missing_confidence"
    ]


def test_missing_model_version_pipeline_output():
    event = DecisionEvent(
        event_id="event_pipeline_008",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version=None,
        error_code=None,
    )

    alert = evaluate_event(event)

    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 1
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "review_missing_or_incomplete_information",
        "no_immediate_action_required",
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "missing_model_version"
    ]

def test_blank_model_version_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "   ",
        error_code = None
    )

    alert = evaluate_event(event)

    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 1
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "review_missing_or_incomplete_information",
        "no_immediate_action_required"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "missing_model_version"
    ]

def test_blank_error_code_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_010",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "   "
    )

    alert = evaluate_event(event)

    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 0
    assert alert.human_required is False
    assert alert.recommended_actions == [
        "no_immediate_action_required"
    ]
    assert alert.signals == []

def test_normalized_decision_type_and_error_code_pipeline_output():
    event = DecisionEvent(
        event_id = "event_pipeline_011",
        decision_type = " APPROVE ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = " GATEWAY_FAILURE "
    )

    alert = evaluate_event(event)

    assert alert.level == "CRITICAL"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 0
    assert alert.human_required is True
    assert alert.recommended_actions == [
        "human_review_required",
        "immediate_investigation",
        "escalate_incident"
    ]
    assert [signal.rule_id for signal in alert.signals] == [
        "evaluation_integrity_override"
    ]
    assert alert.signals[0].evidence == {
        "error_code": "gateway_failure"
    }

def test_invalid_input_stops_pipeline_before_alert_output():
    event = DecisionEvent(
        event_id = "event_pipeline_012",
        decision_type = "approvee",
        confidence = 1.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "decision_type must be one of: approve, reject" in message
    assert "confidence must be between 0.0 and 1.0" in message