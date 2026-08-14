"""End-to-end test: real LLM -> SQL agent -> SSE stream -> persistence.

Requires a valid key in ``backend/.env`` (LLM_API_KEY, or the
OPENCODE_CODEX_API_KEY / DASHSCOPE_API_KEY fallbacks).

Usage:
    cd backend
    ./.venv/bin/python scripts/test_qwen3.py   # connectivity + tool calls
    ./.venv/bin/python scripts/test_nl2sql.py  # NL2SQL agent correctness
    ./.venv/bin/python scripts/test_e2e.py     # full /api/chat pipeline
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

QUESTION = (
    "What are the top 3 products by total quantity sold? "
    "List product name and total quantity."
)


def parse_sse_events(body: str) -> list[tuple[str, str]]:
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


def main() -> int:
    if not (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENCODE_CODEX_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY")
    ):
        print(
            "No LLM API key configured - set LLM_API_KEY in backend/.env "
            "before running the end-to-end test."
        )
        return 2

    with TestClient(app) as client:
        session_id = client.post(
            "/api/sessions", json={"title": "e2e test"}
        ).json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"session_id": session_id, "message": QUESTION},
        ) as response:
            assert response.status_code == 200, response.status_code
            body = "".join(response.iter_text())

        events = parse_sse_events(body)
        kinds = [kind for kind, _ in events]
        for required in ("thinking", "text", "sql", "data", "chart", "done"):
            assert required in kinds, f"missing SSE event: {required}"

        payload = dict(events)
        data = json.loads(payload["data"])
        assert data["columns"], "data event has no columns"
        assert data["rows"], "data event has no rows"
        chart = json.loads(payload["chart"])
        assert chart["type"] in ("bar", "line", "pie"), chart["type"]
        assert chart["data"], "chart event has no data points"

        messages = client.get(f"/api/sessions/{session_id}/messages").json()
        roles = [m["role"] for m in messages]
        assert roles == ["user", "assistant"], roles
        assert messages[-1]["sql_query"], "assistant message has no sql_query"
        assert str(messages[-1]["content"]).strip(), "assistant message is empty"

        client.delete(f"/api/sessions/{session_id}")

    print(
        f"E2E OK: {len(kinds)} events | {len(data['rows'])} rows | "
        f"chart={chart['type']} | sql persisted"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
