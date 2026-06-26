from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context

def build_context(event:DecisionEvent):
    normalized = normalize_event(event)
    return build_evaluation_context(normalized)

def test_no_missing_fields_present():
    event = DecisionEvent(
        event_id = "event_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)
    assert context.field_presence["decision_type"] is True
    assert context.field_presence["confidence"] is True
    assert context.field_presence["latency_ms"] is True
    assert context.field_presence["model_version"] is True

def test_missing_confidence_field():
    event = DecisionEvent(
        event_id = "event_002",
        decision_type = "approve",
        confidence = None,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)
    assert context.field_presence["confidence"] is False
    assert "confidence" in context.missing_fields

def test_missing_decision_type_field():
    event = DecisionEvent(
        event_id = "event_003",
        decision_type = None,
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)
    assert context.field_presence["decision_type"] is False
    assert "decision_type" in context.missing_fields

def test_blank_decision_type_field():
    event = DecisionEvent(
        event_id = "event_004",
        decision_type = None,
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)
    assert context.field_presence["decision_type"] is False
    assert "decision_type" in context.missing_fields

def test_missing_latency_ms_field():
    event = DecisionEvent(
        event_id = "event_005",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = None,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)
    assert context.field_presence["latency_ms"] is False
    assert "latency_ms" in context.missing_fields

def test_missing_model_version_field():
    event = DecisionEvent(
        event_id = "event_006",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = None,
        error_code = None,
    )

    context = build_context(event)
    assert context.field_presence["model_version"] is False
    assert "model_version" in context.missing_fields