from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_missing_required_field():
    payload = {
        # event_id 누락
        "decision_type": "approve",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)

    assert response.status_code == 422

def test_invalid_confidence_field():
    payload = {
        "event_id": "evt_api_test_002",
        "decision_type": "approve",
        "confidence": "high",  # 숫자여야 하지만 문자열 전달
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)

    assert response.status_code == 422

def test_malformed_json():
    response = client.post(
        "/evaluate",
        content='{"event_id": "evt_api_test_003"',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422

