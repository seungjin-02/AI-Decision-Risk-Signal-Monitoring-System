from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_EVALUATE_RESPONSE_KEYS = {
    "trace_id",
    "event_id",
    "level",
    "risk_score",
    "uncertainty_score",
    "human_required",
    "recommended_actions",
    "reason_summary",
    "signals",
    "metadata"
}

EXPECTED_ERROR_RESPONSE_KEYS = {
    "trace_id",
    "error_type",
    "message",
    "details"
}

EXPECTED_SIGNAL_KEYS = {
    "rule_id",
    "category",
    "score",
    "reason",
    "evidence",
    "is_critical_override",
    "metadata"
}

FORBIDDEN_INTERNAL_KEYS = {
    "rule",
    "triggered",
    "boundary",
    "human_review",
    "gate_reason",
    "auto_finalize_allowed",
    "evaluation_limits",
    "field_presence",
    "missing_fields",
    "__dict__",
    "__class__"
}

def assert_trace_id_contract(response, body):
    assert "x-trace-id" in response.headers
    assert "trace_id" in body
    assert body["trace_id"] == response.headers["x-trace-id"]
    assert isinstance(body["trace_id"], str)
    assert body["trace_id"] != ""

def assert_no_forbidden_internal_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert key not in FORBIDDEN_INTERNAL_KEYS
            assert_no_forbidden_internal_keys(value)

    elif isinstance(obj, list):
        for item in obj:
            assert_no_forbidden_internal_keys(item)

def test_success_response():
    payload = {
        "event_id": "evt_response_constraints_001",
        "decision_type": "approve",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {"source": "constraint_test"}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert set(body.keys()) == EXPECTED_EVALUATE_RESPONSE_KEYS
    assert_trace_id_contract(response, body)
    assert_no_forbidden_internal_keys(body)

def test_signal_response_signal_fields():
    payload = {
        "event_id": "evt_response_constraints_002",
        "decision_type": "approve",
        "confidence": 0.6,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert set(signal.keys()) == EXPECTED_SIGNAL_KEYS
    assert_no_forbidden_internal_keys(signal)

def test_error_response_api_validation_error():
    payload = {
        "event_id": "evt_response_constraints_003",
        "decision_type": "approve",
        "confidence": "invalid-confidence",
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert set(body.keys()) == EXPECTED_ERROR_RESPONSE_KEYS
    assert body["error_type"] == "api_validation_error"
    assert_trace_id_contract(response, body)

def test_error_response_core_validation_error():
    payload = {
        "event_id": "evt_response_constraints_004",
        "decision_type": "approve",
        "confidence": 1.5,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert set(body.keys()) == EXPECTED_ERROR_RESPONSE_KEYS
    assert body["error_type"] == "core_validation_error"
    assert_trace_id_contract(response, body)

def test_risk_and_uncertainty_scores():
    payload = {
        "event_id": "evt_response_constraints_005",
        "decision_type": "approve",
        "confidence": 0.6,
        "latency_ms": 300,
        "model_version": None,
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert "risk_score" in body
    assert "uncertainty_score" in body
    assert body["risk_score"] == 3
    assert body["uncertainty_score"] == 1
    assert [signal["category"] for signal in body["signals"]] == ["risk", "uncertainty"]

def test_critical_override():
    payload = {
        "event_id": "evt_response_constraints_006",
        "decision_type": "reject",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": "timeout_01",
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["level"] == "CRITICAL"
    assert body["risk_score"] == 0
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is True
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert signal["rule_id"] == "evaluation_integrity_override"
    assert signal["category"] == "failure"
    assert signal["score"] == 0
    assert signal["is_critical_override"] is True