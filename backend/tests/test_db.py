"""Database initialization smoke tests."""

import sqlite3

from fastapi.testclient import TestClient

from app.db.connection import (
    EXPECTED_EMPLOYEE_ROWS,
    EXPECTED_SALES_ROWS,
    build_sales_seed,
    get_db_path,
    init_sample_database,
)
from app.main import app


def test_sample_database_initialized_on_startup():
    """app.db contains business and metadata tables after startup."""
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        for table in ["sales", "employees", "chat_sessions", "chat_messages"]:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            assert cursor.fetchone() is not None, f"missing table: {table}"
        conn.close()


def test_seed_data_present():
    """sales/employees tables contain seed data."""
    init_sample_database()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sales")
    assert cursor.fetchone()[0] == EXPECTED_SALES_ROWS
    cursor.execute("SELECT COUNT(*) FROM employees")
    assert cursor.fetchone()[0] == EXPECTED_EMPLOYEE_ROWS
    conn.close()


def test_init_is_idempotent():
    """Repeated initialization does not duplicate seed data."""
    init_sample_database()
    init_sample_database()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sales")
    assert cursor.fetchone()[0] == EXPECTED_SALES_ROWS
    cursor.execute("SELECT COUNT(*) FROM employees")
    assert cursor.fetchone()[0] == EXPECTED_EMPLOYEE_ROWS
    conn.close()


def test_sales_seed_is_deterministic_and_rich():
    """The generated seed is stable and covers the full product/month grid."""
    first = build_sales_seed()
    assert first == build_sales_seed()
    assert len(first) == EXPECTED_SALES_ROWS
    months = {row[4] for row in first}
    assert len(months) == 24
    regions = {row[5] for row in first}
    assert regions == {"East", "West", "North", "South"}
