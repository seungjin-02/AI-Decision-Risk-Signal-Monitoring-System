import pytest

from core.step01_DecisionEvent import DecisionEvent
from core.main import evaluate_event

def test_pipeline_validation_error():
    event = DecisionEvent(
        event_id = "evt_invalid_message",
        decision_type = "approve",
        confidence = 1.5,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
    )

    with pytest.raises(ValueError) as exc_info:
        evaluate_event(event)

    message = str(exc_info.value)
    assert "confidence" in message
    assert "Confidence must be between 0.0 and 1.0" in message
    assert "1.5" in message