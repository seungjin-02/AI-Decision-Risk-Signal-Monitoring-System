import pytest
from core.step01_DecisionEvent import DecisionEvent
from core.main import evaluate_event

def test_pipeline_validation_error_for_confidence_above_range():
    event = DecisionEvent(
        event_id = "evt_invalid_confidence",
        decision_type = "approve",
        confidence = 1.5,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "confidence must be between 0.0 and 1.0" in message

def test_pipeline_validation_error_for_blank_decision_type():
    event = DecisionEvent(
        event_id = "evt_invalid_blank_decision_type",
        decision_type = "   ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "decision_type cannot be empty" in message

def test_pipeline_validation_error_for_blank_event_id():
    event = DecisionEvent(
        event_id = "   ",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "event_id must not be empty" in message

def test_pipeline_validation_error_accumulates_multiple_issues():
    event = DecisionEvent(
        event_id = "   ",
        decision_type = "approvee",
        confidence = 1.5,
        latency_ms = -1,
        model_version = "v1",
        error_code = None
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "event_id must not be empty" in message
    assert "decision_type must be one of: approve, reject" in message
    assert "confidence must be between 0.0 and 1.0" in message
    assert "latency ms must be greater than or equal to zero" in message