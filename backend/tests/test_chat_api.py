"""Tests for the /api/chat SSE endpoint (agent is mocked, no LLM calls)."""

import json

import pytest
from fastapi.testclient import TestClient

import app.api.chat as chat_api
from app.main import app


def _sse_events(body: str) -> list[tuple[str, str]]:
    """Parse 'event: X\\ndata: Y' frames from the SSE body."""
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


def _fake_agent_events(question, history):
    """Deterministic fake agent: one tool call, two text deltas, one result."""
    yield {
        "type": "tool_call",
        "tool": "sql_db_query",
        "input": {"query": "SELECT product_name, quantity FROM sales LIMIT 2"},
        "output": "ToolMessage(...)",
    }
    yield {"type": "text_delta", "content": "Top "}
    yield {"type": "text_delta", "content": "products"}
    yield {
        "type": "result",
        "sql": "SELECT product_name, quantity FROM sales LIMIT 2",
        "data": {
            "columns": ["product_name", "quantity"],
            "rows": [["Laptop", 15], ["Mouse", 80]],
            "raw": "[['Laptop', 15], ['Mouse', 80]]",
        },
        "answer": "Top products",
    }


def _new_session(client: TestClient) -> str:
    return client.post("/api/sessions", json={"title": "chat test"}).json()["id"]


@pytest.fixture(autouse=True)
def _mock_agent(monkeypatch):
    """All tests in this module use the fake agent (no real LLM)."""
    monkeypatch.setattr(chat_api, "run_sql_agent", _fake_agent_events)


def test_chat_streams_full_event_sequence():
    """The SSE stream emits thinking -> text -> sql -> data -> chart -> done."""
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "Top products?"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = "".join(response.iter_text())
        events = _sse_events(body)
        kinds = [e for e, _ in events]
        assert kinds == [
            "thinking",
            "text",
            "text",
            "sql",
            "data",
            "chart",
            "done",
        ]

        sql_payload = dict(events)["sql"]
        assert "SELECT product_name" in sql_payload
        data = json.loads(dict(events)["data"])
        assert data["columns"] == ["product_name", "quantity"]
        assert data["rows"][0] == ["Laptop", 15]
        chart = json.loads(dict(events)["chart"])
        assert chart["type"] == "bar"
        assert chart["data"][0]["name"] == "Laptop"


def test_chat_persists_messages_with_sql():
    """The user question and assistant answer (with SQL) are persisted."""
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "Top products?"},
        ):
            pass
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "Top products"
    assert messages[1]["sql_query"] == "SELECT product_name, quantity FROM sales LIMIT 2"
    assert '"columns"' in messages[1]["data_json"]
    assert '"type"' in messages[1]["chart_json"]


def test_chat_persists_executed_sql_in_answer(monkeypatch):
    """The assistant answer's SQL block is replaced by the executed query."""

    def fake_agent_with_wrong_sql(question, history):
        yield {
            "type": "tool_call",
            "tool": "sql_db_query",
            "input": {"query": "SELECT category FROM sales GROUP BY category"},
            "output": "...",
        }
        yield {
            "type": "result",
            "sql": "SELECT category FROM sales GROUP BY category",
            "data": {"columns": ["category"], "rows": [["Electronics"]], "raw": "[]"},
            "answer": "```sql\nSELECT 1 FROM wrong\n```\nInsights.",
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", fake_agent_with_wrong_sql)
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "hi"},
        ):
            pass
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
    content = messages[1]["content"]
    assert "SELECT category FROM sales GROUP BY category" in content
    assert "SELECT 1 FROM wrong" not in content


def test_chat_strips_leading_sql_before_section_1(monkeypatch):
    """A SQL statement placed before section 1 is removed from the answer."""

    def fake_agent(question, history):
        yield {
            "type": "tool_call",
            "tool": "sql_db_query",
            "input": {"query": "SELECT category FROM sales GROUP BY category"},
            "output": "...",
        }
        yield {
            "type": "result",
            "sql": "SELECT category FROM sales GROUP BY category",
            "data": {"columns": ["category"], "rows": [["Electronics"]], "raw": "[]"},
            "answer": (
                "SELECT category FROM sales GROUP BY category\n"
                "1. **Plan** — restate.\n\n"
                "3. **SQL**\n\n```sql\nSELECT category FROM sales GROUP BY category\n```"
            ),
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", fake_agent)
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "hi"},
        ):
            pass
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
    content = messages[1]["content"]
    assert content.startswith("1. **Plan**")
    assert "SELECT category FROM sales GROUP BY category" in content  # section 3 SQL kept


def test_chat_removes_duplicate_sql_from_section_4(monkeypatch):
    """SQL repeated in section 4 prose is removed from the persisted answer."""

    def fake_agent(question, history):
        yield {
            "type": "tool_call",
            "tool": "sql_db_query",
            "input": {"query": "SELECT category FROM sales GROUP BY category"},
            "output": "...",
        }
        yield {
            "type": "result",
            "sql": "SELECT category FROM sales GROUP BY category",
            "data": {"columns": ["category"], "rows": [["Electronics"]], "raw": "[]"},
            "answer": (
                "1. **Plan** — restate.\n\n"
                "3. **SQL**\n\n```sql\nSELECT category FROM sales GROUP BY category\n```\n\n"
                "4. **Execute** — Let me verify it.SELECT category FROM sales GROUP BY "
                "categoryThe query is valid. Now running it."
            ),
        }

    monkeypatch.setattr(chat_api, "run_sql_agent", fake_agent)
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "hi"},
        ):
            pass
        messages = client.get(f"/api/sessions/{session_id}/messages").json()
    content = messages[1]["content"]
    assert content.count("SELECT category FROM sales GROUP BY category") == 1  # fence only
    assert "Let me verify it.\nThe query is valid. Now running it." in content


def test_chat_unknown_session_returns_404():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"session_id": "nope", "message": "hi"},
        )
    assert response.status_code == 404


def test_chat_empty_message_returns_422():
    with TestClient(app) as client:
        session_id = _new_session(client)
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "   "},
        )
    assert response.status_code == 422


def test_chat_error_path_emits_error_then_done(monkeypatch):
    """Agent failures surface as error + done so the client can finish."""

    def failing_agent(question, history):
        yield {"type": "text_delta", "content": "partial"}
        raise RuntimeError("boom")

    monkeypatch.setattr(chat_api, "run_sql_agent", failing_agent)
    with TestClient(app) as client:
        session_id = _new_session(client)
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": "hi"},
        ) as response:
            body = "".join(response.iter_text())
    kinds = [e for e, _ in _sse_events(body)]
    assert kinds == ["text", "error", "done"]
