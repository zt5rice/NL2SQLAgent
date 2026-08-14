"""LangChain SQL agent orchestration (NL2SQL).

Builds a read-only SQL agent from ``SQLDatabaseToolkit`` + ``create_agent`` and
streams its tool-call steps. Model-generated SQL is executed a second time
through a guarded path so the API can return structured ``{columns, rows, raw}``
results. Tool-result strings are parsed with ``ast.literal_eval``, never ``eval``.
"""

import ast
import re
from functools import lru_cache
from typing import Any, Iterator

import sqlalchemy as sa
from langchain.agents import create_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import BaseMessage, HumanMessage

from app.core.database import get_engine, get_sql_database
from app.core.llm import build_system_prompt, get_llm

SQL_QUERY_TOOL = "sql_db_query"
RESULT_LIMIT = 10

# Heading markers and code fences that must start on their own line.
_MARKDOWN_BLOCK_START_RE = re.compile(r"(?<!^)(?<![\n`#])(#{1,6}\s|```)")
# Numbered bold section markers, e.g. "1. **Plan** - ...".
_NUMBERED_SECTION_RE = re.compile(r"(?<!^)(?<![\n`])(\d{1,2}\. \*\*)")

# Defense-in-depth: the agent prompt already forbids writes; this rejects them
# at execution time too (leading keywords, allowing comments/whitespace before).
WRITE_STATEMENT_RE = re.compile(
    r"^\s*(?:INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|VACUUM|TRUNCATE)\b",
    re.IGNORECASE | re.MULTILINE,
)


class ReadOnlyQueryError(ValueError):
    """Raised when model-generated SQL attempts a write statement."""


def normalize_markdown(text: str) -> str:
    """Ensure markdown block markers (headings, code fences) start on a new line.

    Models occasionally glue a heading to the previous sentence (e.g.
    ``"...execute it.## 1. Plan"``), which CommonMark renders as plain text.
    This inserts the missing newline while leaving valid markdown untouched.
    """
    text = _MARKDOWN_BLOCK_START_RE.sub(r"\n\1", text)
    return _NUMBERED_SECTION_RE.sub(r"\n\1", text)


def assert_read_only(sql: str) -> None:
    """Raise ``ReadOnlyQueryError`` when the SQL is not a read-only query."""
    if WRITE_STATEMENT_RE.search(sql or ""):
        raise ReadOnlyQueryError(
            "Read-only constraint: write statements are not allowed."
        )


def parse_literal_result(text: str) -> list | None:
    """Parse a tool-result string (e.g. "[('A', 1), ('B', 2)]") with literal_eval.

    Returns a list only when the text is a safe literal; otherwise None. Never
    uses ``eval``, so arbitrary code in a model/tool result cannot execute.
    """
    try:
        parsed = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError, MemoryError):
        return None
    return parsed if isinstance(parsed, list) else None


def execute_query(sql: str, limit: int = RESULT_LIMIT) -> dict:
    """Execute read-only SQL and return ``{columns, rows, raw}``."""
    assert_read_only(sql)
    with get_engine().connect() as conn:
        result = conn.execute(sa.text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchmany(limit)]
    return {"columns": columns, "rows": rows, "raw": str(rows)}


@lru_cache
def get_sql_agent() -> Any:
    """Cached compiled SQL agent (stateless; state is passed per invocation)."""
    llm = get_llm(streaming=False)
    toolkit = SQLDatabaseToolkit(db=get_sql_database(), llm=llm)
    return create_agent(
        llm,
        toolkit.get_tools(),
        system_prompt=build_system_prompt(dialect="sqlite", top_k=RESULT_LIMIT),
    )


def run_sql_agent(
    question: str, history: list[BaseMessage] | None = None
) -> Iterator[dict]:
    """Run the agent and yield structured events:
    ``{"type": "tool_call", tool, input, output}`` then
    ``{"type": "result", sql, data, answer}``.
    """
    agent = get_sql_agent()
    messages = [*(history or []), HumanMessage(content=question)]
    stream = agent.stream_events({"messages": messages}, version="v3")

    last_sql: str | None = None
    text_parts: list[str] = []

    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            text = item.text if isinstance(item.text, str) else "".join(item.text)
            for token in normalize_markdown(text):
                text_parts.append(token)
                yield {"type": "text_delta", "content": token}
        elif kind == "tool_calls":
            if item.tool_name == SQL_QUERY_TOOL and isinstance(item.input, dict):
                last_sql = item.input.get("query")
            yield {
                "type": "tool_call",
                "tool": item.tool_name,
                "input": item.input,
                "output": item.output,
            }

    data = (
        execute_query(last_sql)
        if last_sql
        else {"columns": [], "rows": [], "raw": ""}
    )
    yield {
        "type": "result",
        "sql": last_sql,
        "data": data,
        "answer": "".join(text_parts),
    }
