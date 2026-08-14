"""Pydantic models for session and message responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    """Create-session request. Title is optional; a default is used when absent."""

    title: str | None = None


class SessionUpdate(BaseModel):
    """Rename-session request."""

    title: str


class SessionOut(BaseModel):
    """Session summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    """A single persisted chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    sql_query: str | None = None
    data_json: str | None = None
    chart_json: str | None = None
    created_at: datetime


class SessionDetail(SessionOut):
    """Session summary plus its full message history."""

    messages: list[MessageOut] = []


class SessionList(BaseModel):
    """List-sessions response."""

    sessions: list[SessionOut]
