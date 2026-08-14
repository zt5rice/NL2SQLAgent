"""Phase 3 acceptance tests: mocked-LLM agent loop, persistence, SSE paths.

These tests exercise the real agent/toolkit wiring with a fake chat model (no
network, no real API key), plus API-level error/read-only/empty-result paths.
"""

import json
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

import app.api.chat as chat_api
import app.core.agent as agent_module
from app.core.agent import run_sql_agent
from app.db import session_store
from app.main import app

FIXED_SQL = (
    "SELECT product_name, SUM(quantity) AS total_quantity FROM sales "
    "GROUP BY product_name ORDER BY total_quantity DESC LIMIT 3"
)


class FakeChatModel(BaseChatModel):
    """Minimal chat model that drives the agent loop deterministically."""

    supports_tool_calling: ClassVar[bool] = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tools = []

    @property
    def _llm_type(self) -> str:
        return "fake-chat"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        self._tools = list(tools)
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        by_name = {m.name for m in tool_messages}
        if "sql_db_query" in by_name:
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content=(
                                "Top products: Ballpoint Pen (500), "
                                "Folder (300), Printer Paper (200)."
                            )
                        )
                    )
                ]
            )
        if "sql_db_schema" in by_name:
            tool_call = {
                "name": "sql_db_query",
                "args": {"query": FIXED_SQL},
                "id": "call_query_1",
                "type": "tool_call",
            }
        elif "sql_db_list_tables" in by_name:
            tool_call = {
                "name": "sql_db_schema",
                "args": {"table_names": "sales"},
                "id": "call_schema_1",
                "type": "tool_call",
            }
        else:
            tool_call = {
                "name": "sql_db_list_tables",
                "args": {},
                "id": "call_tables_1",
                "type": "tool_call",
            }
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))]
        )


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the LLM factory with the deterministic fake model."""
    model = FakeChatModel()
    monkeypatch.setattr(agent_module, "get_llm", lambda streaming=False: model)
    # Drop the cached compiled agent so it rebuilds with the fake model.
    agent_module.get_sql_agent.cache_clear()
    yield model
    agent_module.get_sql_agent.cache_clear()


def _sse_events(body: str) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    current: dict = {}
    for line in body.splitlines():
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = line[6:]
        elif line == "" and current:
            events.append((current.get("event", ""), current.get("data", "")))
            current = {}
    if current:
        events.append((current.get("event", ""), current.get("data", "")))
    return events


def test_agent_loop_with_mocked_llm_runs_real_tools(fake_llm):
    """The full agent loop (list_tables -> schema -> query) works with a fake LLM."""
    events = list(run_sql_agent("What are the top 3 products by quantity sold?"))

    tool_calls = [e for e in events if e["type"] == "tool_call"]
    names = [e["tool"] for e in tool_calls]
    assert names == ["sql_db_list_tables", "sql_db_schema", "sql_db_query"]
    assert tool_calls[-1]["input"]["query"] == FIXED_SQL

    result = events[-1]
    assert result["type"] == "result"
    assert result["sql"] == FIXED_SQL
    assert result["data"]["columns"] == ["product_name", "total_quantity"]
    assert result["data"]["rows"]  # non-empty, top-3 products
    assert isinstance(result["data"]["rows"][0][0], str)
    assert "Top products" in result["answer"]
    assert "".join(e["content"] for e in events if e["type"] == "text_delta") == result["answer"]


def test_chat_sse_with_mocked_llm(fake_llm):
    """/api/chat streams thinking -> text -> sql -> data -> chart -> done."""
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"title": "t"}).json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "Top 3 products?"},
        ) as response:
            body = "".join(response.iter_text())
    kinds = [e for e, _ in _sse_events(body)]
    assert kinds[0] == "thinking"
    assert kinds[-2] == "chart"
    assert kinds[-1] == "done"
    payload = dict(_sse_events(body))
    assert json.loads(payload["data"])["rows"]  # non-empty
    assert json.loads(payload["chart"])["type"] == "pie"


def test_session_persistence_across_restarts():
    """Sessions and messages survive across independent app instances."""
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"title": "persist"}).json()["id"]
        session_store.add_message(session_id, "user", "hello")
        session_store.add_message(session_id, "assistant", "hi")

    # A brand-new client (fresh lifespan) reads the same SQLite file.
    with TestClient(app) as client:
        messages = client.get(f"/api/sessions/{session_id}/messages")
        assert messages.status_code == 200
        assert [m["role"] for m in messages.json()] == ["user", "assistant"]
        client.delete(f"/api/sessions/{session_id}")


def test_chat_memory_window_is_used(fake_llm, monkeypatch):
    """The chat endpoint passes the last 10 rounds (20 messages) as history."""
    captured = {}

    def capturing_agent(question, history):
        captured["history"] = history
        yield {"type": "text_delta", "content": "ok"}
        yield {
            "type": "result",
            "sql": None,
            "data": {"columns": [], "rows": [], "raw": ""},
            "answer": "ok",
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", capturing_agent)
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={}).json()["id"]
        for i in range(12):  # 24 messages = 12 rounds
            session_store.add_message(session_id, "user", f"q{i}")
            session_store.add_message(session_id, "assistant", f"a{i}")
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "next"},
        ):
            pass
    assert len(captured["history"]) == 20
    assert captured["history"][0].content == "q2"


def test_chat_invalid_sql_emits_error(monkeypatch):
    """A failing SQL execution surfaces as error + done, not a 500."""

    def bad_sql_agent(question, history):
        sql = "SELECT * FROM missing_table"
        yield {
            "type": "result",
            "sql": sql,
            "data": agent_module.execute_query(sql),  # raises like run_sql_agent
            "answer": "",
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", bad_sql_agent)
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={}).json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "x"},
        ) as response:
            body = "".join(response.iter_text())
    kinds = [e for e, _ in _sse_events(body)]
    assert kinds == ["error", "done"]


def test_chat_write_sql_is_rejected(monkeypatch):
    """Read-only constraint: write SQL from the model yields an error event."""

    def write_sql_agent(question, history):
        sql = "UPDATE sales SET quantity = 0"
        yield {
            "type": "result",
            "sql": sql,
            "data": agent_module.execute_query(sql),  # raises ReadOnlyQueryError
            "answer": "",
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", write_sql_agent)
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={}).json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "x"},
        ) as response:
            body = "".join(response.iter_text())
    events = _sse_events(body)
    kinds = [e for e, _ in events]
    assert kinds == ["error", "done"]
    assert "Read-only constraint" in dict(events)["error"]


def test_chat_empty_result_still_completes(monkeypatch):
    """Empty query results still emit data + chart + done without crashing."""

    def empty_agent(question, history):
        yield {
            "type": "result",
            "sql": "SELECT product_name FROM sales WHERE 1 = 0",
            "data": {"columns": ["product_name"], "rows": [], "raw": "[]"},
            "answer": "No rows",
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", empty_agent)
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={}).json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "x"},
        ) as response:
            body = "".join(response.iter_text())
    events = _sse_events(body)
    payload = dict(events)
    assert json.loads(payload["data"])["rows"] == []
    assert json.loads(payload["chart"])["data"] == []
    assert events[-1][0] == "done"
