"""Persistence layer for chat sessions and messages (SQLite)."""

import uuid
from datetime import datetime
from typing import Any

from app.db.connection import get_raw_connection

DEFAULT_SESSION_TITLE = "New Session"


def _row_to_session(row: Any) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "created_at": _parse_timestamp(row[2]),
        "updated_at": _parse_timestamp(row[3]),
    }


def _row_to_message(row: Any) -> dict:
    return {
        "id": row[0],
        "session_id": row[1],
        "role": row[2],
        "content": row[3],
        "sql_query": row[4],
        "created_at": _parse_timestamp(row[5]),
    }


def _parse_timestamp(value: str | None) -> datetime:
    """SQLite CURRENT_TIMESTAMP yields 'YYYY-MM-DD HH:MM:SS' (UTC, naive)."""
    return datetime.fromisoformat(value) if value else datetime.utcnow()


def create_session(title: str | None = None) -> dict:
    """Create a session and return its row."""
    session_id = uuid.uuid4().hex
    with get_raw_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title) VALUES (?, ?)",
            (session_id, title or DEFAULT_SESSION_TITLE),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row)


def list_sessions() -> list[dict]:
    """All sessions, most recently updated first."""
    with get_raw_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions "
            "ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_session(row) for row in rows]


def get_session(session_id: str) -> dict | None:
    """One session row, or None when it does not exist."""
    with get_raw_connection() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row) if row else None


def rename_session(session_id: str, title: str) -> dict | None:
    """Rename a session and bump updated_at. Returns None when not found."""
    with get_raw_connection() as conn:
        cursor = conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (title, session_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row)


def delete_session(session_id: str) -> bool:
    """Delete a session (messages cascade). Returns False when not found."""
    with get_raw_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()
    return cursor.rowcount > 0


def touch_session(session_id: str) -> None:
    """Bump updated_at after new activity (best effort if session is gone)."""
    with get_raw_connection() as conn:
        conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        conn.commit()


def list_messages(session_id: str) -> list[dict]:
    """Messages for a session in chronological order."""
    with get_raw_connection() as conn:
        rows = conn.execute(
            "SELECT id, session_id, role, content, sql_query, created_at "
            "FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [_row_to_message(row) for row in rows]


def add_message(
    session_id: str, role: str, content: str, sql_query: str | None = None
) -> dict:
    """Persist a message; raises ValueError when the session does not exist."""
    if get_session(session_id) is None:
        raise ValueError(f"Session '{session_id}' does not exist")
    with get_raw_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, sql_query) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, sql_query),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, session_id, role, content, sql_query, created_at "
            "FROM chat_messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    touch_session(session_id)
    return _row_to_message(row)
