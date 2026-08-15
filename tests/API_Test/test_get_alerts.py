from datetime import datetime
from fastapi.testclient import TestClient
from app.db.alert_repository import AlertRepository
from app.main import app
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent

client = TestClient(app)

def test_get_alert_by_id_returns_stored_alert(test_db_path):
    repository = AlertRepository(test_db_path)

    event = DecisionEvent(
        event_id="event_get_alert_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "get_alert_api_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_get_alert_001",
    )

    response = client.get(f"/alerts/{saved.alert_id}")

    assert response.status_code == 200
    assert "x-trace-id" in response.headers
    assert response.headers["x-trace-id"]

    body = response.json()

    assert set(body.keys()) == {
        "alert_id",
        "trace_id",
        "created_at",
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

    assert body["alert_id"] == saved.alert_id
    assert body["trace_id"] == "trace_get_alert_001" # alert를 생성했던 과거 POST 평가 흐름의 trace_id
    assert body["event_id"] == alert.event_id
    assert body["level"] == alert.level
    assert body["risk_score"] == alert.risk_score
    assert body["uncertainty_score"] == alert.uncertainty_score
    assert body["human_required"] is alert.human_required
    assert body["recommended_actions"] == alert.recommended_actions
    assert body["reason_summary"] == alert.reason_summary
    assert body["metadata"] == alert.metadata

    expected_signals = [
        {
            "rule_id": signal.rule_id,
            "category": signal.category,
            "score": signal.score,
            "reason": signal.reason,
            "evidence": signal.evidence,
            "is_critical_override": signal.is_critical_override,
            "metadata": signal.metadata,
        }
        for signal in alert.signals
    ]

    assert body["signals"] == expected_signals

    assert body["trace_id"] != response.headers["x-trace-id"]

    # Pydantic이 datetime으로 검증한 뒤 ISO 문자열로 직렬화한다.
    response_created_at = datetime.fromisoformat(body["created_at"].replace("Z", "+00:00"))
    saved_created_at = datetime.fromisoformat(saved.created_at)

    assert response_created_at == saved_created_at

def test_get_alert_by_id_returns_404_when_alert_does_not_exist(test_db_path,):
    missing_alert_id = 999

    response = client.get(f"/alerts/{missing_alert_id}")

    assert response.status_code == 404
    assert "x-trace-id" in response.headers

    body = response.json()

    assert set(body.keys()) == {
        "trace_id",
        "error_type",
        "message",
        "details",
    }

    assert body["error_type"] == "alert_not_found"
    assert body["message"] == "Alert not found"
    assert body["details"] == [
        {
            "alert_id": missing_alert_id,
        }
    ]

    assert body["trace_id"] == response.headers["x-trace-id"]