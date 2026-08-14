"""Tests for the database introspection endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_tables_list_excludes_internal_tables():
    """chat_sessions / chat_messages are never exposed as business tables."""
    with _client() as client:
        response = client.get("/api/database/tables")
    assert response.status_code == 200
    tables = response.json()["tables"]
    assert "sales" in tables
    assert "employees" in tables
    assert "chat_sessions" not in tables
    assert "chat_messages" not in tables


def test_schema_endpoint_returns_structured_schema():
    """Schema includes column metadata, sample rows, and row counts."""
    with _client() as client:
        response = client.get("/api/database/schema")
    assert response.status_code == 200
    payload = response.json()
    sales = next(t for t in payload["tables"] if t["name"] == "sales")
    assert sales["row_count"] == 15
    names = {c["name"] for c in sales["columns"]}
    assert {"product_name", "category", "quantity", "price"} <= names
    assert len(sales["sample_rows"]) > 0
    assert "product_name" in sales["sample_rows"][0]


def test_table_detail_endpoint():
    """GET /api/database/tables/{name} returns one table's detail."""
    with _client() as client:
        response = client.get("/api/database/tables/employees")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "employees"
    assert payload["row_count"] == 8


def test_table_detail_unknown_table_returns_404():
    """Unknown tables return 404, not a raw SQL error."""
    with _client() as client:
        response = client.get("/api/database/tables/does_not_exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
