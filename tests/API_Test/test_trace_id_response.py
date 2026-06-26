from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_trace_id_exists_in_success_response_and_header():
    payload = {
        "event_id": "evt_trace_success",
        "decision_type": "approve",
        "confidence": 0.52,
        "latency_ms": 2800,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }
    response = client.post("/evaluate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "trace_id" in body
    assert "x-trace-id" in response.headers


def test_trace_id_exists_in_api_validation_error_response_and_header():
    payload = {
        "event_id": "evt_trace_error",
        "decision_type": "approve",
        "confidence": "abc",
        "latency_ms": 2800,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }
    response = client.post("/evaluate", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert "trace_id" in body
    assert "x-trace-id" in response.headers