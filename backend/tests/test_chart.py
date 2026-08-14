"""Tests for the chart heuristic module."""

from app.core.chart import PIE_MAX_GROUPS, suggest_chart
from app.schemas.chat import QueryResult


def _result(columns, rows):
    return QueryResult(columns=columns, rows=rows)


def test_group_by_few_rows_uses_pie():
    """GROUP BY with ≤6 groups suggests a pie chart."""
    rows = [[f"cat{i}", i] for i in range(4)]
    config = suggest_chart(
        "SELECT category, SUM(quantity) FROM sales GROUP BY category",
        _result(["category", "total"], rows),
    )
    assert config.type == "pie"
    assert config.x_field == "category"
    assert config.y_field == "total"
    assert len(config.data) == 4
    assert config.data[0].name == "cat0"
    assert config.data[0].value == 0


def test_group_by_many_rows_uses_bar():
    """GROUP BY with more than 6 groups falls back to a bar chart."""
    rows = [[f"cat{i}", i] for i in range(PIE_MAX_GROUPS + 3)]
    config = suggest_chart(
        "SELECT category, COUNT(*) FROM sales GROUP BY category",
        _result(["category", "cnt"], rows),
    )
    assert config.type == "bar"


def test_order_by_limit_uses_bar():
    """ORDER BY + LIMIT queries suggest a bar chart."""
    rows = [["A", 10], ["B", 20]]
    config = suggest_chart(
        "SELECT product_name, quantity FROM sales ORDER BY quantity DESC LIMIT 5",
        _result(["product_name", "quantity"], rows),
    )
    assert config.type == "bar"
    assert config.data[0].name == "A"
    assert config.data[0].value == 10


def test_plain_select_defaults_to_bar():
    """Queries without GROUP BY default to a bar chart."""
    config = suggest_chart(
        "SELECT product_name, price FROM sales",
        _result(["product_name", "price"], [["Laptop", 5999.0]]),
    )
    assert config.type == "bar"


def test_numeric_axis_selection_prefers_last_numeric_column():
    """The last numeric column is chosen as the metric when available."""
    rows = [[f"p{i}", i, i * 10] for i in range(3)]
    config = suggest_chart(
        "SELECT product_name, quantity, price FROM sales",
        _result(["product_name", "quantity", "price"], rows),
    )
    assert config.y_field == "price"
    assert config.data[0].name == "p0"
    assert config.data[0].value == 0  # second column is used for the value


def test_single_column_rows():
    """Rows with one column still produce usable data points."""
    config = suggest_chart(
        "SELECT COUNT(*) FROM sales",
        _result(["cnt"], [[42]]),
    )
    assert config.type == "bar"
    assert config.data[0].value == 42


def test_empty_result():
    """Empty results produce a bar config with no data (no crash)."""
    config = suggest_chart("SELECT 1 FROM sales LIMIT 0", _result(["x"], []))
    assert config.type == "bar"
    assert config.data == []


def test_sse_serialization_uses_camel_case_aliases():
    """model_dump_for_sse emits xField/yField for the frontend contract."""
    config = suggest_chart(
        "SELECT category, SUM(quantity) FROM sales GROUP BY category",
        _result(["category", "total"], [["A", 1]]),
    )
    payload = config.model_dump_for_sse()
    assert "xField" in payload
    assert "yField" in payload
    assert "x_field" not in payload
