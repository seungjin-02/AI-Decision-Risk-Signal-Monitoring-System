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

def assert_core_validation_error_response(response, body):
    assert response.status_code == 400
    assert set(body.keys()) == EXPECTED_ERROR_RESPONSE_KEYS
    assert body["error_type"] == "core_validation_error"
    assert isinstance(body["message"], str)
    assert body["message"] != ""
    assert body["details"] == []
    assert_trace_id_contract(response, body)

    for key in ALERT_RESPONSE_KEYS:
        assert key not in body

def test_core_validation_rejects_confidence_above_allowed_range():
    payload = {
        "event_id": "evt_core_validation_001",
        "decision_type": "approve",
        "confidence": 1.5,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "confidence" in body["message"]

def test_core_validation_rejects_confidence_below_allowed_range():
    payload = {
        "event_id": "evt_core_validation_002",
        "decision_type": "approve",
        "confidence": -0.1,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "confidence" in body["message"]

def test_core_validation_rejects_blank_event_id():
    payload = {
        "event_id": "   ",
        "decision_type": "approve",
        "confidence": 0.9,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "event_id" in body["message"]

def test_core_validation_rejects_blank_decision_type():
    payload = {
        "event_id": "evt_core_validation_004",
        "decision_type": "   ",
        "confidence": 0.9,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "decision_type" in body["message"]

def test_core_validation_unsupported_decision_type():
    payload = {
        "event_id": "evt_core_validation_005",
        "decision_type": "pending",
        "confidence": 0.9,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "decision_type" in body["message"]

def test_core_validation_rejects_negative_latency_ms():
    payload = {
        "event_id": "evt_core_validation_006",
        "decision_type": "approve",
        "confidence": 0.9,
        "latency_ms": -1,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_core_validation_error_response(response, body)
    assert "latency_ms" in body["message"]

def test_core_validation_multiple_errors():
    payload = {
        "event_id": "   ",
        "decision_type": "pending",
        "confidence": 1.5,
        "latency_ms": -1,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert_core_validation_error_response(response, body)
    assert "event_id" in body["message"]
    assert "decision_type" in body["message"]
    assert "confidence" in body["message"]
    assert "latency_ms" in body["message"]