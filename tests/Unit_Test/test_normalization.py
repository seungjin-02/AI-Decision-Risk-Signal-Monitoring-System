from core.step01_DecisionEvent import DecisionEvent
from core.step02_NormalizedEvent import normalize_event

def test_normalize_event_id():
    event = DecisionEvent(
        event_id = " evt_001 ",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.event_id == "evt_001"

def test_normalize_decision_type():
    event = DecisionEvent(
        event_id = "evt_002",
        decision_type = " APPROVE ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.decision_type == "approve"

def test_normalize_model_version():
    event = DecisionEvent(
        event_id = "evt_003",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = " Model-V1 ",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.model_version == "Model-V1"

def test_normalize_error_code():
    event = DecisionEvent(
        event_id = "evt_004",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = " GATEWAY_FAILURE "
    )

    normalized = normalize_event(event)

    assert normalized.error_code == "gateway_failure"

def test_blank_optional_operational_string_fields():
    event = DecisionEvent(
        event_id = "evt_005",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "   ",
        error_code = "   ",
    )

    normalized = normalize_event(event)

    assert normalized.model_version is None
    assert normalized.error_code is None

def test_none_optional_fields():
    event = DecisionEvent(
        event_id = "evt_006",
        decision_type = None,
        confidence = None,
        latency_ms = None,
        model_version = None,
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.decision_type is None
    assert normalized.confidence is None
    assert normalized.latency_ms is None
    assert normalized.model_version is None
    assert normalized.error_code is None

def test_confidence_int_is_normalized_to_float():
    event = DecisionEvent(
        event_id = "evt_007",
        decision_type = "approve",
        confidence = 1,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.confidence == 1.0

def test_confidence_float_remains_float():
    event = DecisionEvent(
        event_id = "evt_008",
        decision_type = "approve",
        confidence = 0.52,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.confidence == 0.52

def test_latency_ms_remains_int():
    event = DecisionEvent(
        event_id = "evt_009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 2800,
        model_version = "v1",
        error_code = None
    )

    normalized = normalize_event(event)

    assert normalized.latency_ms == 2800

def test_metadata():
    metadata = {
        "request_id": "req_001",
        "source": "unit_test"
    }

    event = DecisionEvent(
        event_id = "evt_010",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
        metadata = metadata
    )

    normalized = normalize_event(event)

    assert normalized.metadata == {
        "request_id": "req_001",
        "source": "unit_test",
    }
    assert normalized.metadata is not metadata