import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def create_connection(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.row_factory = sqlite3.Row

    return connection

def init_db(db_path: str | Path) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = create_connection(db_path)

    try:
        connection.executescript("BEGIN;\n" + schema_sql)
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()