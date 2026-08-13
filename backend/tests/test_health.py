"""健康检查与 CORS 冒烟测试。"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    """GET /health 返回 200 与 status=ok。"""
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_headers_present_for_allowed_origin():
    """允许的 CORS 来源应收到 access-control-allow-origin 头。"""
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
