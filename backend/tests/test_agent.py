"""Unit tests for the SQL agent orchestration (no real LLM calls)."""

import pytest

from app.core import agent
from app.core.database import get_sql_database


def test_assert_read_only_rejects_writes():
    """DML/DDL statements are rejected; SELECT queries pass."""
    for bad in [
        "INSERT INTO sales (product_name) VALUES ('x')",
        "  UPDATE sales SET quantity = 1",
        "DELETE FROM sales",
        "DROP TABLE sales",
        "-- comment\nALTER TABLE sales ADD COLUMN x",
    ]:
        with pytest.raises(agent.ReadOnlyQueryError):
            agent.assert_read_only(bad)
    agent.assert_read_only("SELECT * FROM sales")
    agent.assert_read_only("WITH top AS (SELECT 1) SELECT * FROM top")


def test_parse_literal_result_uses_safe_eval():
    """Tool-result strings parse to rows; dangerous text never executes."""
    assert agent.parse_literal_result("[('A', 1), ('B', 2)]") == [
        ("A", 1),
        ("B", 2),
    ]
    assert agent.parse_literal_result("not a literal") is None
    # A code object is not a list, so literal_eval safely returns None.
    assert agent.parse_literal_result("__import__('os').system('echo hi')") is None
    assert agent.parse_literal_result("[]") == []


def test_execute_query_returns_structured_rows():
    """Valid read-only SQL yields columns/rows/raw with a bounded limit."""
    result = agent.execute_query(
        "SELECT product_name, quantity FROM sales ORDER BY quantity DESC"
    )
    assert result["columns"] == ["product_name", "quantity"]
    assert len(result["rows"]) == agent.RESULT_LIMIT
    assert result["rows"][0][0] == "Ballpoint Pen"
    assert "Ballpoint Pen" in result["raw"]


def test_execute_query_rejects_writes():
    """execute_query refuses write statements before touching the DB."""
    with pytest.raises(agent.ReadOnlyQueryError):
        agent.execute_query("DELETE FROM sales")


def test_toolkit_exposes_expected_tools():
    """The SQL toolkit exposes the four tools used by the agent loop."""
    toolkit_tools = [
        "sql_db_list_tables",
        "sql_db_schema",
        "sql_db_query",
        "sql_db_query_checker",
    ]
    llm = __import__("app.core.llm", fromlist=["get_llm"]).get_llm(streaming=False)
    from langchain_community.agent_toolkits import SQLDatabaseToolkit

    toolkit = SQLDatabaseToolkit(db=get_sql_database(), llm=llm)
    names = [t.name for t in toolkit.get_tools()]
    assert sorted(names) == sorted(toolkit_tools)


def test_get_sql_agent_builds_without_network():
    """Compiling the agent requires no LLM call."""
    compiled = agent.get_sql_agent()
    assert compiled is not None
