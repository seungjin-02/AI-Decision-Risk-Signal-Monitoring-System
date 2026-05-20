import pytest
from step01_DecisionEvent import DecisionEvent
from main import evaluate_event

def test_normal_case():
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
    assert "no_immediate_action_required" in alert.recommended_actions

def test_low_confidence():
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
    assert "monitor_closely" in alert.recommended_actions

def test_high_latency():
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
    assert "monitor_closely" in alert.recommended_actions

def test_high_risk_without_uncertainty():
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
    assert "human_review_required" in alert.recommended_actions
    assert "escalate_incident" in alert.recommended_actions

def test_high_risk_with_uncertainty():
    event = DecisionEvent(
        event_id = "event_pipeline_005",
        decision_type = "approve",
        confidence = 0.3,
        latency_ms = 2800,
        model_version = " ",
        error_code = None
    )

    alert = evaluate_event(event)
    assert alert.level == "WARN"
    assert alert.risk_score == 5
    assert alert.uncertainty_score == 1
    assert alert.human_required is True
    assert "human_review_required" in alert.recommended_actions
    assert "review_missing_or_incomplete_information" in alert.recommended_actions
    assert "monitor_closely" in alert.recommended_actions

def test_high_risk_override():
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
    assert "human_review_required" in alert.recommended_actions
    assert "immediate_investigation" in alert.recommended_actions
    assert "escalate_incident" in alert.recommended_actions

def test_missing_confidence():
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
    assert "review_missing_or_incomplete_information" in alert.recommended_actions
    assert "no_immediate_action_required" in alert.recommended_actions

def test_missing_model_version():
    event = DecisionEvent(
        event_id = "event_pipeline_008",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    alert = evaluate_event(event)
    assert alert.level == "INFO"
    assert alert.risk_score == 0
    assert alert.uncertainty_score == 1
    assert alert.human_required is False
    assert "review_missing_or_incomplete_information" in alert.recommended_actions
    assert "no_immediate_action_required" in alert.recommended_actions

def test_invalid_input():
    event = DecisionEvent(
        event_id = "event_pipeline_009",
        decision_type = "approvee",
        confidence = 1.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    with pytest.raises(ValueError):
        evaluate_event(event)
























