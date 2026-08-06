from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_confidence_pass_threshold():
    payload = {
        "event_id": "event_core_validation_001",
        "decision_type": "approve",
        "confidence": 0.8,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200

def test_confidence_above_threshold():
    payload = {
        "event_id": "event_core_validation_002",
        "decision_type": "approve",
        "confidence": 1.5,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "confidence" in body["message"]

def test_confidence_below_threshold():
    payload = {
        "event_id": "event_core_validation_003",
        "decision_type": "approve",
        "confidence": -0.1,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "confidence" in body["message"]

def test_blank_event_id():
    payload = {
        "event_id": "   ",
        "decision_type": "approve",
        "confidence": 0.8,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "event_id" in body["message"]

def test_blank_decision_type():
    payload = {
        "event_id": "event_core_validation_005",
        "decision_type": "   ",
        "confidence": 0.8,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "decision_type" in body["message"]

def test_unsupported_decision_type():
    payload = {
        "event_id": "event_core_validation_006",
        "decision_type": "unknown",
        "confidence": 0.8,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "decision_type" in body["message"]

def test_negative_latency_ms():
    payload = {
        "event_id": "event_core_validation_007",
        "decision_type": "approve",
        "confidence": 0.8,
        "latency_ms": -1,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 400
    assert body["error_type"] == "core_validation_error"
    assert "latency_ms" in body["message"]
