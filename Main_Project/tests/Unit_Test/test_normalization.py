from step01_DecisionEvent import DecisionEvent
from step02_NormalizedEvent import normalize_event


def test_normalize_string_fields():
    event = DecisionEvent(
        event_id=" evt_001 ",
        decision_type=" APPROVE ",
        confidence=0.9,
        latency_ms=800,
        model_version=" v1 ",
        error_code=" GATEWAY_FAILURE ",
    )

    normalized = normalize_event(event)

    assert normalized.event_id == "evt_001"
    assert normalized.decision_type == "approve"
    assert normalized.model_version == "v1"
    assert normalized.error_code == "gateway_failure"


def test_normalize_numeric_string_fields():
    event = DecisionEvent(
        event_id="evt_002",
        decision_type="approve",
        confidence="0.52",
        latency_ms="2800",
        model_version="v1",
        error_code=None,
    )

    normalized = normalize_event(event)

    assert normalized.confidence == 0.52
    assert normalized.latency_ms == 2800
    assert isinstance(normalized.confidence, float)
    assert isinstance(normalized.latency_ms, int)


def test_empty_optional_strings_become_none():
    event = DecisionEvent(
        event_id="evt_003",
        decision_type="   ",
        confidence=0.9,
        latency_ms=800,
        model_version="   ",
        error_code="   ",
    )

    normalized = normalize_event(event)

    assert normalized.decision_type is None
    assert normalized.model_version is None
    assert normalized.error_code is None


def test_metadata_is_copied():
    metadata = {"request_id": "req_001"}

    event = DecisionEvent(
        event_id="evt_004",
        decision_type="approve",
        confidence=0.9,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata=metadata,
    )

    normalized = normalize_event(event)

    assert normalized.metadata == {"request_id": "req_001"}
    assert normalized.metadata is not metadata