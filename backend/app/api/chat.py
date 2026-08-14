"""Chat endpoint: POST /api/chat streams SSE events.

Event sequence: ``thinking`` (tool progress) -> ``text`` (answer deltas) ->
``sql`` -> ``data`` (``{columns, rows, raw}``) -> ``chart`` -> ``done``;
errors are emitted as ``error`` followed by ``done``.
"""

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core import memory
from app.core.agent import run_sql_agent
from app.core.chart import suggest_chart
from app.db import session_store

router = APIRouter(prefix="/api/chat", tags=["chat"])

_STOP = object()


class ChatRequest(BaseModel):
    """POST /api/chat request body."""

    session_id: str
    message: str = Field(..., min_length=1)


def _sse(event: str, data: str) -> dict:
    """SSE frame for sse-starlette."""
    return {"event": event, "data": data}


def _next_event(iterator) -> object:
    """next() that returns a sentinel instead of raising StopIteration,
    because StopIteration cannot propagate through asyncio.to_thread futures."""
    try:
        return next(iterator)
    except StopIteration:
        return _STOP


@router.post("")
async def chat(payload: ChatRequest) -> EventSourceResponse:
    """Run the SQL agent for a session and stream the SSE response."""
    if session_store.get_session(payload.session_id) is None:
        raise HTTPException(
            status_code=404, detail=f"Session '{payload.session_id}' not found"
        )
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message must not be empty")

    # Rebuild prior history first (cache-fresh), then persist the new user turn.
    # run_sql_agent appends the current question itself, so history must not
    # include it - otherwise the model would see the question twice.
    memory.invalidate(payload.session_id)
    history = memory.get_history_messages(payload.session_id)
    session_store.add_message(payload.session_id, "user", message)
    memory.invalidate(payload.session_id)

    return EventSourceResponse(
        _chat_events(payload.session_id, message, history),
        ping=15,
    )


async def _chat_events(
    session_id: str, question: str, history: list
) -> AsyncIterator[dict]:
    """Stream agent events as SSE frames, persisting the assistant reply."""
    sql: str | None = None
    try:
        # The agent performs blocking LLM/tool calls; run it in a worker thread.
        agent_iter = run_sql_agent(question, history)
        while True:
            event = await asyncio.to_thread(_next_event, agent_iter)
            if event is _STOP:
                break

            if event["type"] == "tool_call":
                if event["tool"] == "sql_db_query" and isinstance(event["input"], dict):
                    sql = event["input"].get("query")
                yield _sse("thinking", f"Calling tool: {event['tool']}")
            elif event["type"] == "text_delta":
                yield _sse("text", event["content"])
            elif event["type"] == "result":
                answer = event["answer"]
                session_store.add_message(
                    session_id, "assistant", answer, sql_query=sql
                )
                memory.invalidate(session_id)
                if sql:
                    yield _sse("sql", sql)
                yield _sse("data", json.dumps(event["data"], ensure_ascii=False))
                chart = suggest_chart(sql, event["data"])
                yield _sse(
                    "chart",
                    json.dumps(chart.model_dump_for_sse(), ensure_ascii=False),
                )

        yield _sse("done", "")
    except Exception as exc:  # surface model/tool failures as error + done
        yield _sse("error", str(exc))
        yield _sse("done", "")
