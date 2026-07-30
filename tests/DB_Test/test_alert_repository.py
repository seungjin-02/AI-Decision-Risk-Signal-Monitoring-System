import json
from app.db.connection import create_connection, init_db
from app.db.alert_repository import AlertRepository
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent

def test_save_stores_alert_row(tmp_path):
    db_path = tmp_path / 'test.db'
    init_db(db_path)
    repository = AlertRepository(db_path)

    event = DecisionEvent(
        event_id="event_repository_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_test",
        },
    )

    alert = evaluate_event(event)
    assert alert.event_id == "event_repository_001"
    assert alert.level == "WARN"
    assert alert.risk_score == 3
    assert alert.uncertainty_score == 0
    assert alert.human_required is False
    assert alert.recommended_actions == ["monitor_closely"]
    assert alert.reason_summary == (
        "medium risk with low uncertainty can be handled "
        "as warning-level interpretation"
    )
    assert alert.metadata == {
        "source": "repository_test",
    }

    assert len(alert.signals) == 1

    signal = alert.signals[0]

    assert signal.rule_id == "approve_confidence_low"
    assert signal.category == "risk"
    assert signal.score == 3
    assert signal.reason == "approve decision with low confidence"
    assert signal.evidence == {
        "decision_type": "approve",
        "confidence": 0.3,
    }
    assert signal.is_critical_override is False
    assert signal.metadata == {}
    saved = repository.save(
        alert=alert,
        trace_id="trace_test_001",
    )

    connection = create_connection(db_path)

    try:
        alert_row = connection.execute(
            """
            SELECT
                alert_id,
                trace_id,
                event_id,
                level,
                risk_score,
                uncertainty_score,
                human_required,
                reason_summary,
                metadata,
                created_at
            FROM alerts
            WHERE alert_id = ?
            """,
            (saved.alert_id,),
        ).fetchone()

        assert alert_row is not None
        assert alert_row["alert_id"] == saved.alert_id
        assert alert_row["trace_id"] == "trace_test_001"
        assert alert_row["event_id"] == alert.event_id
        assert alert_row["level"] == alert.level
        assert alert_row["risk_score"] == alert.risk_score
        assert alert_row["uncertainty_score"] == alert.uncertainty_score
        assert alert_row["human_required"] == int(alert.human_required)
        assert alert_row["reason_summary"] == alert.reason_summary
        assert json.loads(alert_row["metadata"]) == alert.metadata
        assert alert_row["created_at"]

    finally:
        connection.close()


