"""Database introspection endpoints."""

from fastapi import APIRouter, HTTPException

from app.core.database import get_table_detail, list_tables
from app.schemas.database import DatabaseSchema, TableSchema, TablesResponse

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/tables", response_model=TablesResponse)
def get_tables() -> TablesResponse:
    """List business tables (internal chat_* tables are excluded)."""
    return TablesResponse(tables=list_tables())


@router.get("/schema", response_model=DatabaseSchema)
def get_schema() -> DatabaseSchema:
    """Full schema (columns, sample rows, row counts) for all business tables."""
    tables = [table for name in list_tables() if (table := get_table_detail(name))]
    return DatabaseSchema(tables=tables)


@router.get("/tables/{name}", response_model=TableSchema)
def get_table(name: str) -> TableSchema:
    """Schema and sample rows for a single table."""
    table = get_table_detail(name)
    if table is None:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    return table
