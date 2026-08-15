import json
import sqlite3
import pytest

from app.db.alert_repository import AlertDetail, PersistenceError
from app.db.connection import create_connection
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent

def test_save_stores_alert_row(repository, test_db_path):
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

    connection = create_connection(test_db_path)

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
            (saved.alert_id,)
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

def test_save_stores_signal_row(repository, test_db_path):
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

    connection = create_connection(test_db_path)

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
            (saved.alert_id,)
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

def test_save_stores_action_row(repository, test_db_path):
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

    connection = create_connection(test_db_path)

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

def test_save_rollback(repository, test_db_path):
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

    # 동일한 rule_id를 가진 signal을 의도적으로 중복 추가
    alert.signals.append(alert.signals[0])

    with pytest.raises(PersistenceError) as exc_info:
        repository.save(
            alert=alert,
            trace_id="trace_test_004",
        )

    # PersistenceError가 원래 IntegrityError를 보존하는지 검증
    assert isinstance(exc_info.value.__cause__, sqlite3.IntegrityError)

    connection = create_connection(test_db_path)

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

def test_find_by_id_returns_none_when_alert_does_not_exist(repository):
    result = repository.find_by_id(alert_id=999)

    assert result is None

def test_find_by_id_returns_existing_alert(repository):
    event = DecisionEvent(
        event_id="event_find_by_id_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_find_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_find_by_id_001",
    )

    result = repository.find_by_id(
        alert_id=saved.alert_id,
    )

    assert result is not None
    assert result.alert_id == saved.alert_id
    assert result.trace_id == "trace_find_by_id_001"
    assert result.event_id == alert.event_id
    assert result.level == alert.level
    assert result.risk_score == alert.risk_score
    assert result.uncertainty_score == alert.uncertainty_score
    assert result.human_required is alert.human_required
    assert result.reason_summary == alert.reason_summary
    assert result.metadata == alert.metadata
    assert result.created_at == saved.created_at
    assert result.recommended_actions == alert.recommended_actions
    assert result.signals == alert.signals
    assert isinstance(result.human_required, bool)
    assert isinstance(result.metadata, dict)
    for signal in result.signals:
        assert isinstance(signal.is_critical_override, bool)
        assert isinstance(signal.evidence, dict)
        assert isinstance(signal.metadata, dict)

def test_find_recent_returns_empty_list_when_database_is_empty(repository):
    results = repository.find_recent(limit=10)

    assert results == []

def test_find_recent_out_of_limit_range_raise_value_error(repository):
    for invalid_limit in 0, 101:
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            repository.find_recent(limit=invalid_limit)

def test_find_recent_applies_limit_and_preserves_alert_details(repository):
    first_event = DecisionEvent(
        event_id="event_find_recent_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_find_test1",
        },
    )

    first_alert = evaluate_event(first_event)

    first_saved = repository.save(
        alert=first_alert,
        trace_id="trace_find_recent_001",
    )

    second_event = DecisionEvent(
        event_id="event_find_recent_002",
        decision_type="approve",
        confidence=0.8,
        latency_ms=1800,
        model_version="v2",
        error_code=None,
        metadata={
            "source": "repository_find_test2",
        },
    )

    second_alert = evaluate_event(second_event)

    second_saved = repository.save(
        alert=second_alert,
        trace_id="trace_find_recent_002",
    )

    result_by_one = repository.find_recent(limit=1)

    assert len(result_by_one) == 1

    result = result_by_one[0]

    assert result.alert_id == second_saved.alert_id
    assert result.trace_id == "trace_find_recent_002"
    assert result.event_id == second_alert.event_id
    assert result.level == second_alert.level
    assert result.risk_score == second_alert.risk_score
    assert result.uncertainty_score == second_alert.uncertainty_score
    assert result.human_required is second_alert.human_required
    assert result.reason_summary == second_alert.reason_summary
    assert result.metadata == second_alert.metadata
    assert result.created_at == second_saved.created_at
    assert result.recommended_actions == second_alert.recommended_actions
    assert result.signals == second_alert.signals

    result_by_two = repository.find_recent(limit=2)

    assert len(result_by_two) == 2

    recent_result, older_result = result_by_two

    assert recent_result.alert_id == second_saved.alert_id
    assert older_result.alert_id == first_saved.alert_id
    assert recent_result.signals == second_alert.signals
    assert recent_result.recommended_actions == second_alert.recommended_actions
    assert older_result.signals == first_alert.signals
    assert older_result.recommended_actions == first_alert.recommended_actions