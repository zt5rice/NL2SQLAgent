"""Database initialization smoke tests."""

import sqlite3
from itertools import islice

from fastapi.testclient import TestClient

from app.db.connection import (
    EXPECTED_EMPLOYEE_ROWS,
    EXPECTED_SALES_ROWS,
    build_sales_seed,
    get_db_path,
    init_sample_database,
)
from app.db.session_store import add_message, create_session, delete_session
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
    """The generated seed is stable, ~1M rows, and covers all months/regions."""
    sample = list(islice(build_sales_seed(), 2000))
    assert len(sample) == 2000
    assert sample == list(islice(build_sales_seed(), 2000))

    total = 0
    months: set[str] = set()
    regions: set[str] = set()
    for row in build_sales_seed():
        total += 1
        months.add(row[4][:7])
        regions.add(row[5])
    assert total == EXPECTED_SALES_ROWS
    assert EXPECTED_SALES_ROWS > 1_000_000
    assert len(months) == 24
    assert regions == {"East", "West", "North", "South"}


def test_legacy_glued_headings_are_normalized_on_startup():
    """Old assistant messages with glued headings are fixed by the migration."""
    session_id = create_session("migration test")["id"]
    try:
        add_message(session_id, "assistant", "Run it.## 1. Plan\nBody text.")
        init_sample_database()  # triggers the legacy normalization
        conn = sqlite3.connect(get_db_path())
        content = conn.execute(
            "SELECT content FROM chat_messages WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchone()[0]
        conn.close()
        assert "Run it.\n\n## 1. Plan" in content

        # Idempotent: a second run changes nothing.
        init_sample_database()
        conn = sqlite3.connect(get_db_path())
        content_again = conn.execute(
            "SELECT content FROM chat_messages WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchone()[0]
        conn.close()
        assert content_again == content
    finally:
        delete_session(session_id)
