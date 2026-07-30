import json
import sqlite3
import pytest
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

def test_save_stores_signal_row(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    repository = AlertRepository(db_path)

    event = DecisionEvent(
        event_id="event_repository_002",
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

    saved = repository.save(
        alert=alert,
        trace_id="trace_test_002",
    )

    connection = create_connection(db_path)

    try:
        signal_rows = connection.execute(
            """
            SELECT
                signal_id,
                alert_id,
                rule_id,
                category,
                score,
                reason,
                evidence,
                is_critical_override,
                metadata
            FROM alert_signals
            WHERE alert_id = ?
            ORDER BY signal_id
            """,
            (saved.alert_id,),
        ).fetchall()

        assert len(signal_rows) == len(alert.signals)

        for signal_row, signal in zip(signal_rows, alert.signals):
            assert signal_row["signal_id"] is not None
            assert signal_row["alert_id"] == saved.alert_id
            assert signal_row["rule_id"] == signal.rule_id
            assert signal_row["category"] == signal.category
            assert signal_row["score"] == signal.score
            assert signal_row["reason"] == signal.reason
            assert json.loads(signal_row["evidence"]) == signal.evidence
            assert signal_row["is_critical_override"] == int(signal.is_critical_override)
            assert json.loads(signal_row["metadata"]) == signal.metadata

    finally:
        connection.close()

def test_save_stores_action_row(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    repository = AlertRepository(db_path)

    event = DecisionEvent(
        event_id="event_repository_003",
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

    saved = repository.save(
        alert=alert,
        trace_id="trace_test_003",
    )

    connection = create_connection(db_path)

    try:
        action_rows = connection.execute(
            """
            SELECT
                action_id,
                alert_id,
                action_code,
                action_order
            FROM alert_actions
            WHERE alert_id = ?
            ORDER BY action_order
            """,
            (saved.alert_id,),
        ).fetchall()

        assert len(action_rows) == len(alert.recommended_actions)

        for expected_order, action_row in enumerate(action_rows):
            action_code = alert.recommended_actions[expected_order]

            assert action_row["action_id"] is not None
            assert action_row["alert_id"] == saved.alert_id
            assert action_row["action_code"] == action_code
            assert action_row["action_order"] == expected_order

    finally:
        connection.close()

def test_save_rollback(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    repository = AlertRepository(db_path)

    event = DecisionEvent(
        event_id="event_repository_004",
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
    alert.signals.append(alert.signals[0]) # 의도적 중복 추가

    with pytest.raises(sqlite3.IntegrityError):
        repository.save(
            alert=alert,
            trace_id="trace_test_004",
        )

    connection = create_connection(db_path)

    try:
        alert_count = connection.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

        signal_count = connection.execute(
            "SELECT COUNT(*) FROM alert_signals"
        ).fetchone()[0]

        action_count = connection.execute(
            "SELECT COUNT(*) FROM alert_actions"
        ).fetchone()[0]

        assert alert_count == 0
        assert signal_count == 0
        assert action_count == 0

    finally:
        connection.close()