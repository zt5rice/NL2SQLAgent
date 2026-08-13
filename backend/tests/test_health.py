"""Health check and CORS smoke tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    """GET /health returns 200 with status=ok."""
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_headers_present_for_allowed_origin():
    """Allowed CORS origin receives the access-control-allow-origin header."""
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
