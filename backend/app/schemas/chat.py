"""Pydantic models shared by the chat SSE endpoint and chart heuristics."""

from pydantic import BaseModel, ConfigDict, Field


class ChartDataPoint(BaseModel):
    """One data point for the chart: category name + value."""

    name: str
    value: int | float | str


class ChartConfig(BaseModel):
    """Chart configuration consumed by the frontend ChartPanel.

    ``xField`` / ``yField`` are serialized with camelCase aliases to match the
    frontend TypeScript contract (``ChartConfig.xField`` / ``ChartConfig.yField``).
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = "bar"  # bar | line | pie | table
    title: str = "Query result"
    data: list[ChartDataPoint] = []
    x_field: str | None = Field(default=None, alias="xField")
    y_field: str | None = Field(default=None, alias="yField")

    def model_dump_for_sse(self) -> dict:
        """Serialize with camelCase aliases for the SSE ``chart`` event."""
        return self.model_dump(by_alias=True)


class QueryResult(BaseModel):
    """Structured query result for the SSE ``data`` event."""

    columns: list[str] = []
    rows: list[list] = []
    raw: str = ""
