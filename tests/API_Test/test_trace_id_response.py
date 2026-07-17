from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def assert_trace_id_contract(response, body):
    assert "x-trace-id" in response.headers
    assert "trace_id" in body
    assert body["trace_id"] == response.headers["x-trace-id"]
    assert isinstance(body["trace_id"], str)
    assert body["trace_id"] != ""

def test_trace_id_is_returned_for_successful_evaluate_response():
    payload = {
        "event_id": "evt_trace_001",
        "decision_type": "approve",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert response.status_code == 200
    assert_trace_id_contract(response, body)

def test_trace_id_is_returned_for_api_validation_error():
    payload = {
        "event_id": "evt_trace_002",
        "decision_type": "approve",
        "confidence": "not-a-number",
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert response.status_code == 422
    assert body["error_type"] == "api_validation_error"
    assert_trace_id_contract(response, body)

def test_trace_id_is_returned_for_core_validation_error():
    payload = {
        "event_id": "evt_trace_003",
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
    assert body["error_type"] == "core_validation_error"
    assert_trace_id_contract(response, body)

def test_trace_id_is_returned_for_health_response():
    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert_trace_id_contract(response, body)

def test_trace_id_is_unique_per_request():
    first_response = client.get("/health")
    second_response = client.get("/health")

    first_body = first_response.json()
    second_body = second_response.json()

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert_trace_id_contract(first_response, first_body)
    assert_trace_id_contract(second_response, second_body)

    assert first_body["trace_id"] != second_body["trace_id"]
    assert first_response.headers["x-trace-id"] != second_response.headers["x-trace-id"]