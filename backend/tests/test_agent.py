"""Unit tests for the SQL agent orchestration (no real LLM calls)."""

import pytest

from app.core import agent
from app.core.database import get_sql_database
from app.core.markdown import MarkdownStreamNormalizer, replace_sql_block


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


def test_normalize_markdown_glued_heading_gets_newline():
    """A heading glued to the previous sentence is moved to its own line."""
    text = "The query is valid. Let me execute it.## 1. Plan\nThe question asks..."
    normalized = agent.normalize_markdown(text)
    assert "it.\n## 1. Plan" in normalized
    assert "it.## 1. Plan" not in normalized


def test_normalize_markdown_keeps_valid_markdown_unchanged():
    """Properly formatted headings, fences, and tables are untouched."""
    text = "## 1. Plan\n\nBody\n\n```sql\nSELECT 1\n```\n\n## 2. Explore"
    assert agent.normalize_markdown(text) == text


def test_normalize_markdown_glued_code_fence_gets_newline():
    """Code fences glued to prose are moved to their own line."""
    normalized = agent.normalize_markdown("The query:```sql\nSELECT 1\n```")
    assert "\n```sql" in normalized


def test_normalize_markdown_no_leading_blank_line():
    """A heading at the very start keeps no leading newline."""
    assert agent.normalize_markdown("## 1. Plan\nBody").startswith("## ")


def test_normalize_markdown_glued_numbered_section_gets_newline():
    """Numbered bold sections glued to prose are moved to their own line."""
    normalized = agent.normalize_markdown("LIMIT 3;1. **Plan** — restate the question.")
    assert "LIMIT 3;\n1. **Plan**" in normalized


def test_normalize_markdown_keeps_existing_numbered_sections():
    """Numbered sections already at line start stay untouched."""
    text = "## 5. Results\n\n1. **Plan** — restate the question."
    assert agent.normalize_markdown(text) == text


def test_replace_sql_block_uses_executed_query():
    """The ```sql fence content is replaced with the executed query."""
    answer = "## 3. SQL\n\n```sql\nSELECT 1 FROM wrong\n```\n\nInsights."
    replaced = replace_sql_block(answer, "SELECT category FROM sales GROUP BY category")
    assert "SELECT category FROM sales GROUP BY category" in replaced
    assert "SELECT 1 FROM wrong" not in replaced


def test_replace_sql_block_falls_back_to_sql_looking_fence():
    """A generic fence whose content looks like SQL is replaced too."""
    answer = "```\nSELECT * FROM sales\n```\nDone."
    replaced = replace_sql_block(answer, "SELECT category FROM sales")
    assert "SELECT category FROM sales" in replaced
    assert "SELECT * FROM sales" not in replaced


def test_replace_sql_block_ignores_non_sql_or_missing():
    """No SQL (or no SQL-looking block) means the answer is unchanged."""
    answer = "Some text without a code block."
    assert replace_sql_block(answer, "SELECT 1") == answer
    assert replace_sql_block("```sql\nSELECT 1\n```", None) == "```sql\nSELECT 1\n```"


def test_normalize_markdown_closing_fence_glue():
    """A closing fence glued to a section marker gets a newline."""
    normalized = agent.normalize_markdown("```1. **Plan** — restate.")
    assert "```\n1. **Plan**" in normalized


def test_markdown_stream_normalizer_fixes_glue_across_events():
    """A glued section marker spanning stream events is normalized."""
    normalizer = MarkdownStreamNormalizer()
    chunks = normalizer.push("SELECT ... ORDER BY total_quantity DESC")
    chunks += normalizer.push(";1. **Plan** — restate the question.")
    tail = normalizer.finish()
    joined = "".join(chunks + [tail])
    assert "DESC;\n1. **Plan**" in joined
    assert "DESC;1. **Plan" not in joined


def test_markdown_stream_normalizer_emits_complete_lines():
    """Only complete lines are emitted; the tail comes from finish()."""
    normalizer = MarkdownStreamNormalizer()
    assert normalizer.push("line one\n") == ["line one\n"]
    assert normalizer.push("line two") == []
    assert normalizer.finish() == "line two"


def test_execute_query_returns_structured_rows():
    """Valid read-only SQL yields columns/rows/raw with a bounded limit."""
    result = agent.execute_query(
        "SELECT product_name, SUM(quantity) AS total FROM sales "
        "GROUP BY product_name ORDER BY total DESC"
    )
    assert result["columns"] == ["product_name", "total"]
    assert len(result["rows"]) == agent.RESULT_LIMIT
    totals = [row[1] for row in result["rows"]]
    assert totals == sorted(totals, reverse=True)
    assert isinstance(result["rows"][0][0], str)
    assert result["raw"].startswith("[['")


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
