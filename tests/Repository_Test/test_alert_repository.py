import sqlite3
import pytest
from app.db.connection import init_db, create_connection
from app.db.alert_repository import AlertRepository
from core.step05_SignalGeneration import Signal
from core.step09_AlertOutput import AlertOutput

def test_alert_repository_success(tmp_path):
    db_path = tmp_path / "test_alert_repository.db"
    init_db(db_path)
    repository = AlertRepository(db_path)

    signal = Signal(
        rule_id="test_001",
        category="risk",
        score=5,
        reason="test risk signal override",
        evidence={
            "risk_value": 5
        },
        is_critical_override=False,
        metadata={
            "source": "repository_test"
        },
    )

    alert = AlertOutput(
        event_id="event_test_001",
        level="CRITICAL",
        risk_score=5,
        uncertainty_score=0,
        human_required=True,
        recommended_actions=[
            "human_review_required",
            "escalate_incident"
        ],
        reason_summary="test alert",
        signals=[signal],
        metadata={
            "source": "repository_test"
        },
    )

    trace_id = "trace_success_test_001"

    saved = repository.save(
        alert=alert,
        trace_id=trace_id,
    )

    connection = create_connection(db_path)

    try:
        alert_row = connection.execute(
            "SELECT * FROM alerts WHERE alert_id = ?",
            (saved.alert_id,),
        ).fetchone() # 조회결과 중 행 하나 반환

        signal_row = connection.execute(
            "SELECT * FROM alert_signals WHERE alert_id = ?",
            (saved.alert_id,),
        ).fetchone()

        action_rows = connection.execute(
            """
            SELECT *
            FROM alert_actions
            WHERE alert_id = ?
            ORDER BY action_order
            """,
            (saved.alert_id,),
        ).fetchall()  # 조회결과 중 남아있는 행 전부 반환

    finally:
        connection.close()

    assert saved.alert_id > 0
    assert alert_row is not None
    assert alert_row["event_id"] == alert.event_id
    assert alert_row["trace_id"] == trace_id
    assert signal_row is not None
    assert signal_row["rule_id"] == signal.rule_id
    assert len(action_rows) == len(alert.recommended_actions)
    assert [row["action_word"] for row in action_rows] == alert.recommended_actions

def test_alert_repository_rollback(tmp_path):
    db_path = tmp_path / "test_alert_repository.db"
    init_db(db_path)
    repository = AlertRepository(db_path)

    signal = Signal(
        rule_id="test_rollback_001",
        category="risk",
        score=5,
        reason="rollback test",
        evidence={"risk_value": 5},
        is_critical_override=False,
        metadata={"source": "rollback-test"},
    )

    alert = AlertOutput(
        event_id="event-rollback-001",
        level="CRITICAL",
        risk_score=5,
        uncertainty_score=0,
        human_required=True,
        recommended_actions=[
            "human_review_required",
            "escalate_incident"
        ],
        reason_summary="rollback test alert",
        signals=[signal, signal],
        metadata={"source": "rollback-test"},
    )

    trace_id = "trace_rollback_test-001"

    with pytest.raises(sqlite3.IntegrityError):
        repository.save(
            alert=alert,
            trace_id=trace_id,
    )

    connection = create_connection(db_path)

    try:
        alert_count = connection.execute(
            """
            SELECT COUNT(*) AS count 
            FROM alerts
            """
        ).fetchone()["count"]

        signal_count = connection.execute(
            """
            SELECT COUNT(*) AS count 
            FROM alert_signals
            """
        ).fetchone()["count"]

        action_count = connection.execute(
            """
            SELECT COUNT(*) AS count 
            FROM alert_actions
            """
        ).fetchone()["count"]

    finally:
        connection.close()

    assert alert_count == 0
    assert signal_count == 0
    assert action_count == 0
