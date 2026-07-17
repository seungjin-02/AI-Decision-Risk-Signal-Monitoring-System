from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_ERROR_RESPONSE_KEYS = {
    "trace_id",
    "error_type",
    "message",
    "details"
}

ALERT_RESPONSE_KEYS = {
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

def assert_trace_id_contract(response, body):
    assert "x-trace-id" in response.headers
    assert "trace_id" in body
    assert body["trace_id"] == response.headers["x-trace-id"]
    assert isinstance(body["trace_id"], str)
    assert body["trace_id"] != ""

def assert_api_validation_error_response(response, body):
    assert response.status_code == 422
    assert set(body.keys()) == EXPECTED_ERROR_RESPONSE_KEYS
    assert body["error_type"] == "api_validation_error"
    assert body["message"] == "Request format or type is invalid."
    assert isinstance(body["details"], list)
    assert len(body["details"]) >= 1
    assert_trace_id_contract(response, body)

    for key in ALERT_RESPONSE_KEYS:
        assert key not in body

def test_api_validation_rejects_non_numeric_confidence():
    payload = {
        "event_id": "evt_api_validation_001",
        "decision_type": "approve",
        "confidence": "not-a-number",
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_api_validation_error_response(response, body)

def test_api_validation_rejects_non_integer_latency_ms():
    payload = {
        "event_id": "evt_api_validation_002",
        "decision_type": "approve",
        "confidence": 0.9,
        "latency_ms": "slow",
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_api_validation_error_response(response, body)

def test_api_validation_rejects_non_string_event_id():
    payload = {
        "event_id": 1234,
        "decision_type": "approve",
        "confidence": 0.9,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_api_validation_error_response(response, body)

def test_api_validation_rejects_non_object_metadata():
    payload = {
        "event_id": "evt_api_validation_004",
        "decision_type": "approve",
        "confidence": 0.9,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": "not-an-object",
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_api_validation_error_response(response, body)