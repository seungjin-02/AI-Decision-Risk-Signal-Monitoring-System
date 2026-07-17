from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event
from core.step03_EvaluationContext import build_evaluation_context

def build_context(event: DecisionEvent):
    normalized = normalize_event(event)
    return build_evaluation_context(normalized)

def test_all_required_fields_present():
    event = DecisionEvent(
        event_id = "evt_context_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence == {
        "decision_type": True,
        "confidence": True,
        "latency_ms": True,
        "model_version": True,
        "error_code": False
    }
    assert context.missing_fields == []
    assert context.evaluation_limits == []

def test_missing_confidence():
    event = DecisionEvent(
        event_id = "evt_context_002",
        decision_type = "approve",
        confidence = None,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["confidence"] is False
    assert "confidence" in context.missing_fields
    assert "approve_confidence_rule_blocked" in context.evaluation_limits

def test_missing_decision_type():
    event = DecisionEvent(
        event_id = "evt_context_003",
        decision_type = None,
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["decision_type"] is False
    assert "decision_type" in context.missing_fields
    assert "decision_type_dependent_rules_blocked" in context.evaluation_limits

def test_missing_latency_ms():
    event = DecisionEvent(
        event_id = "evt_context_004",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = None,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["latency_ms"] is False
    assert "latency_ms" in context.missing_fields

def test_missing_model_version():
    event = DecisionEvent(
        event_id = "evt_context_005",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = None,
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["model_version"] is False
    assert "model_version" in context.missing_fields

def test_blank_model_version():
    event = DecisionEvent(
        event_id = "evt_context_006",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "   ",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["model_version"] is False
    assert "model_version" in context.missing_fields

def test_error_code():
    event = DecisionEvent(
        event_id = "evt_context_007",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = None
    )

    context = build_context(event)

    assert context.field_presence["error_code"] is False
    assert "error_code" not in context.missing_fields
    assert context.missing_fields == []

def test_blank_error_code():
    event = DecisionEvent(
        event_id = "evt_context_008",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = "   "
    )

    context = build_context(event)

    assert context.field_presence["error_code"] is False
    assert "error_code" not in context.missing_fields
    assert context.evaluation_limits == []

def test_present_error_code():
    event = DecisionEvent(
        event_id = "evt_context_009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 500,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    context = build_context(event)

    assert context.field_presence["error_code"] is True
    assert "error_code" not in context.missing_fields

def test_multiple_missing_fields_accumulate_context_information():
    event = DecisionEvent(
        event_id = "evt_context_010",
        decision_type = None,
        confidence = None,
        latency_ms = None,
        model_version = None,
        error_code = None
    )

    context = build_context(event)

    assert context.missing_fields == [
        "decision_type",
        "confidence",
        "latency_ms",
        "model_version"
    ]
    assert context.evaluation_limits == [
        "approve_confidence_rule_blocked",
        "decision_type_dependent_rules_blocked"
    ]