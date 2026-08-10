import pytest

from app.db.alert_repository import AlertRepository
from app.db.connection import init_db

@pytest.fixture
def test_db_path(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path

@pytest.fixture
def repository(test_db_path):
    return AlertRepository(test_db_path)