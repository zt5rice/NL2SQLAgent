"""Database access wrapper (LangChain SQLDatabase) and schema introspection.

The application's own metadata tables (``chat_sessions`` / ``chat_messages``)
are excluded from the wrapper so the LLM agent never sees or queries them.
"""

from functools import lru_cache
from typing import Any

import sqlalchemy as sa

from app.config import get_settings
from app.schemas.database import ColumnInfo, TableSchema

# Metadata tables managed by the application itself - not business data.
INTERNAL_TABLES = {"chat_sessions", "chat_messages"}


@lru_cache
def _introspection_engine() -> sa.Engine:
    """SQLAlchemy engine used for structured schema introspection."""
    from app.db.connection import get_db_path

    return sa.create_engine(f"sqlite:///{get_db_path()}")


def get_engine() -> sa.Engine:
    """Public access to the cached SQLAlchemy engine (read-only queries)."""
    return _introspection_engine()


@lru_cache
def get_sql_database() -> Any:
    """Cached LangChain ``SQLDatabase`` for the configured SQLite file."""
    from langchain_community.utilities import SQLDatabase

    settings = get_settings()
    return SQLDatabase.from_uri(
        settings.database_url,
        ignore_tables=sorted(INTERNAL_TABLES),
        sample_rows_in_table_info=3,
    )


def list_tables() -> list[str]:
    """Business table names, sorted, excluding internal metadata tables."""
    return sorted(get_sql_database().get_usable_table_names())


def get_table_detail(table: str) -> TableSchema | None:
    """Structured schema + sample rows for one table, or None if unknown."""
    db = get_sql_database()
    usable = db.get_usable_table_names()
    if table not in usable:
        return None

    engine = _introspection_engine()
    inspector = sa.inspect(engine)
    pk_columns = set(
        inspector.get_pk_constraint(table).get("constrained_columns", [])
    )
    columns = [
        ColumnInfo(
            name=col["name"],
            type=str(col["type"]),
            nullable=bool(col.get("nullable", True)),
            default=str(col["default"]) if col.get("default") is not None else None,
            primary_key=col["name"] in pk_columns,
        )
        for col in inspector.get_columns(table)
    ]

    with engine.connect() as conn:
        row_count = int(conn.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0)
        sample_rows = [
            dict(row)
            for row in conn.execute(sa.text(f'SELECT * FROM "{table}" LIMIT 5')).mappings()
        ]

    return TableSchema(
        name=table,
        columns=columns,
        sample_rows=sample_rows,
        row_count=row_count,
    )
