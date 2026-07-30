import sqlite3
import pytest
from app.db.connection import create_connection, init_db

def test_init_db_create_all_tables(tmp_path):
    db_path = tmp_path / 'test.db'
    init_db(db_path)
    connection = create_connection(db_path)

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name IN ('alerts', 'alert_signals', 'alert_actions')
            """
        ).fetchall()

        table_names = {row["name"] for row in rows}

        assert table_names == {
            "alerts",
            "alert_signals",
            "alert_actions",
        }

    finally:
        connection.close()

def test_init_db_rollback_all_tables_on_schema_error(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    broken_schema_path = tmp_path / "broken_schema.sql"

    broken_schema_path.write_text(
        """
        CREATE TABLE alerts (
            alert_id INTEGER PRIMARY KEY
        );

        CREATE TABL alert_signals (
            signal_id INTEGER PRIMARY KEY
        );
        """,
        encoding="utf-8",
    )

    # SCHEMA_PATH를 찾아서 테스트 중에만 broken_schema_path로 교체
    monkeypatch.setattr(
        "app.db.connection.SCHEMA_PATH",
        broken_schema_path,
    )

    with pytest.raises(sqlite3.OperationalError):
        init_db(db_path)

    # rollback 결과를 확인하기 위한 connection
    connection = create_connection(db_path)

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('alerts', 'alert_signals')
            """
        ).fetchall()

        table_names = {row["name"] for row in rows}

        assert table_names == set()
    finally:
        connection.close()

def test_create_connection_enables_foreign_keys(tmp_path):
    db_path = tmp_path / "test.db"
    connection = create_connection(db_path)

    try:
        row = connection.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1

    finally:
        connection.close()

def test_create_connection_uses_row_factory(tmp_path):
    db_path = tmp_path / "test.db"
    connection = create_connection(db_path)

    try:
        row = connection.execute(
            "SELECT 123 AS test_value"
        ).fetchone()

        assert isinstance(row, sqlite3.Row)
        assert row["test_value"] == 123

    finally:
        connection.close()

def test_foreign_key_rejects_signal_without_alert(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    connection = create_connection(db_path)

    try:
        with pytest.raises(
            sqlite3.IntegrityError,
            match="FOREIGN KEY constraint failed",
        ):
            connection.execute(
                """
                INSERT INTO alert_signals (
                    alert_id,
                    rule_id,
                    category,
                    score,
                    reason,
                    evidence,
                    is_critical_override,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    999999,
                    "test-rule-001",
                    "risk",
                    5,
                    "pytest test",
                    "{}",
                    0,
                    "{}",
                ),
            )

        row = connection.execute(
            "SELECT COUNT(*) AS count FROM alert_signals"
        ).fetchone()

        assert row["count"] == 0
    finally:
        connection.rollback()
        connection.close()