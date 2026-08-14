"""Tests for the session management API and its persistence."""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _unique_title() -> str:
    return f"Test Session {uuid.uuid4().hex[:8]}"


def test_create_and_list_sessions():
    """POST /api/sessions creates a session; it appears in the list."""
    title = _unique_title()
    with _client() as client:
        response = client.post("/api/sessions", json={"title": title})
        assert response.status_code == 201
        created = response.json()
        assert created["title"] == title
        assert created["id"]

        listed = client.get("/api/sessions").json()["sessions"]
        assert any(s["id"] == created["id"] for s in listed)

        client.delete(f"/api/sessions/{created['id']}")


def test_create_session_default_title():
    """Omitting the title falls back to a default."""
    with _client() as client:
        response = client.post("/api/sessions", json={})
    assert response.status_code == 201
    assert response.json()["title"] == "New Session"
    session_id = response.json()["id"]
    with _client() as client:
        client.delete(f"/api/sessions/{session_id}")


def test_rename_session():
    """PUT /api/sessions/{id} updates the title."""
    with _client() as client:
        created = client.post("/api/sessions", json={"title": "Before"}).json()
        renamed = client.put(
            f"/api/sessions/{created['id']}", json={"title": "After"}
        )
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "After"
        client.delete(f"/api/sessions/{created['id']}")


def test_message_persistence_and_query():
    """Messages persist and are returned in order."""
    with _client() as client:
        session_id = client.post("/api/sessions", json={}).json()["id"]
        from app.db.session_store import add_message

        add_message(session_id, "user", "What are the top products?")
        add_message(session_id, "assistant", "Here are the results.", "SELECT 1")

        messages = client.get(f"/api/sessions/{session_id}/messages")
        assert messages.status_code == 200
        payload = messages.json()
        assert [m["role"] for m in payload] == ["user", "assistant"]
        assert payload[1]["sql_query"] == "SELECT 1"

        detail = client.get(f"/api/sessions/{session_id}").json()
        assert len(detail["messages"]) == 2

        client.delete(f"/api/sessions/{session_id}")


def test_delete_session_and_404s():
    """Unknown sessions return 404; deletion cascades to messages."""
    with _client() as client:
        missing = client.get("/api/sessions/does-not-exist")
        assert missing.status_code == 404

        created = client.post("/api/sessions", json={}).json()
        session_id = created["id"]
        deleted = client.delete(f"/api/sessions/{session_id}")
        assert deleted.status_code == 204

        assert client.get(f"/api/sessions/{session_id}").status_code == 404
        assert client.get(f"/api/sessions/{session_id}/messages").status_code == 404
