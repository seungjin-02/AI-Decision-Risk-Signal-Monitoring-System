from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_evaluate_endpoint():
    payload = {
        "event_id": "evt_api_test_001",
        "decision_type": "approve",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["event_id"] == payload["event_id"]

    required_fields = {
        "trace_id",
        "event_id",
        "level",
        "risk_score",
        "uncertainty_score",
        "human_required",
        "recommended_actions",
        "reason_summary",
        "signals",
        "metadata",
    }

    assert required_fields.issubset(body.keys())
