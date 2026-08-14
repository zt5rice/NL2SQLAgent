"""Session management endpoints."""

from fastapi import APIRouter, HTTPException, Response, status

from app.db import session_store
from app.schemas.session import (
    MessageOut,
    SessionCreate,
    SessionDetail,
    SessionList,
    SessionOut,
    SessionUpdate,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _require_session(session_id: str) -> dict:
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@router.get("", response_model=SessionList)
def get_sessions() -> SessionList:
    """List all sessions, most recently updated first."""
    return SessionList(sessions=session_store.list_sessions())


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate) -> dict:
    """Create a new session."""
    return session_store.create_session(payload.title)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session_detail(session_id: str) -> SessionDetail:
    """Session detail including its message history."""
    _require_session(session_id)
    return SessionDetail(
        **session_store.get_session(session_id),
        messages=session_store.list_messages(session_id),
    )


@router.put("/{session_id}", response_model=SessionOut)
def update_session(session_id: str, payload: SessionUpdate) -> dict:
    """Rename a session."""
    _require_session(session_id)
    return session_store.rename_session(session_id, payload.title)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str) -> Response:
    """Delete a session and its messages."""
    _require_session(session_id)
    session_store.delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def get_session_messages(session_id: str) -> list[dict]:
    """Message history for a session, in chronological order."""
    _require_session(session_id)
    return session_store.list_messages(session_id)
