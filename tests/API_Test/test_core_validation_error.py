from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_core_validation_error_does_not_enter_rule_evaluation():
    payload = {
        "event_id": "evt_001",
        "decision_type": "approve",
        "confidence": 1.5,
        "latency_ms": 2800,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }
    response = client.post("/evaluate", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error_type"] == "core_validation_error"
    assert "trace_id" in body
    assert "message" in body
    assert "risk_score" not in body
    assert "uncertainty_score" not in body
    assert "signals" not in body
    assert "human_required" not in body
    assert "recommended_actions" not in body