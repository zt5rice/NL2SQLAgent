"""Chart type and axis heuristics for query results.

Rules (from the phase plan):
- GROUP BY with ≤ 6 result rows -> pie
- GROUP BY with > 6 rows, or ORDER BY + LIMIT -> bar
- anything else -> bar (the frontend can still switch to line/pie/table)
"""

from app.schemas.chat import ChartConfig, ChartDataPoint, QueryResult

PIE_MAX_GROUPS = 6


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _pick_axis_fields(columns: list[str], rows: list[list]) -> tuple[str | None, str | None]:
    """Choose x/y columns: first column as dimension, last numeric as metric."""
    if not columns:
        return None, None
    x_field = columns[0]
    # Prefer the last column whose sample value is numeric.
    y_field = columns[-1]
    for index in range(len(columns) - 1, 0, -1):
        values = [row[index] for row in rows if index < len(row)]
        if values and all(_is_numeric(v) for v in values[:5]):
            y_field = columns[index]
            break
    return x_field, y_field


def _to_data_points(rows: list[list], x_field: str | None, y_field: str | None) -> list[ChartDataPoint]:
    points: list[ChartDataPoint] = []
    for index, row in enumerate(rows):
        if not row:
            continue
        if len(row) >= 2:
            name, value = str(row[0]), row[1]
        else:
            name, value = (str(row[0]) if x_field else str(index)), row[0]
        points.append(ChartDataPoint(name=name, value=value))
    return points


def suggest_chart(sql: str | None, result: QueryResult | dict) -> ChartConfig:
    """Pick a chart type and build the config from SQL shape + result rows."""
    columns = result["columns"] if isinstance(result, dict) else result.columns
    rows = result["rows"] if isinstance(result, dict) else result.rows
    sql_lower = (sql or "").lower()
    row_count = len(rows)

    if "group by" in sql_lower and 0 < row_count <= PIE_MAX_GROUPS:
        chart_type = "pie"
    else:
        chart_type = "bar"

    x_field, y_field = _pick_axis_fields(columns, rows)
    return ChartConfig(
        type=chart_type,
        title="Query result",
        data=_to_data_points(rows, x_field, y_field),
        x_field=x_field,
        y_field=y_field,
    )
