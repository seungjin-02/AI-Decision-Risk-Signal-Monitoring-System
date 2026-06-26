from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_validation_error_does_not_create_risk_result():
    payload = {
        "event_id": "evt_001",
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
    assert body["error_type"] == "api_validation_error"
    assert "trace_id" in body
    assert "details" in body
    assert "risk_score" not in body
    assert "uncertainty_score" not in body
    assert "signals" not in body
    assert "human_required" not in body
    assert "recommended_actions" not in body