"""Session-wide test setup: ensure the sample database exists and is seeded."""

import pytest

from app.db.connection import ensure_data_dir, init_sample_database


@pytest.fixture(scope="session", autouse=True)
def _seed_sample_database():
    """Initialize the SQLite file once before any test touches it."""
    ensure_data_dir()
    init_sample_database()
    yield
