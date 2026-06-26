from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_evaluate_response_does_not_include_forbidden_fields():
    payload = {
        "event_id": "evt_001",
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
    forbidden_fields = {
        "priority",
        "combined_score",
        "final_decision",
        "auto_approve",
        "auto_reject",
        "approval_result",
        "rejection_result",
    }
    for field in forbidden_fields:
        assert field not in body


def test_evaluate_response_keeps_risk_and_uncertainty_separated():
    payload = {
        "event_id": "evt_002",
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
    assert "risk_score" in body
    assert "uncertainty_score" in body
    assert "combined_score" not in body