"""Pydantic models for database introspection responses."""

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    """A single database column."""

    name: str
    type: str
    nullable: bool = True
    default: str | None = None
    primary_key: bool = False


class TableSchema(BaseModel):
    """Schema and sample rows for one table."""

    name: str
    columns: list[ColumnInfo]
    sample_rows: list[dict] = []
    row_count: int = 0


class DatabaseSchema(BaseModel):
    """Schema for every business table."""

    tables: list[TableSchema]


class TablesResponse(BaseModel):
    """List of business table names."""

    tables: list[str]
