"""Scratch test: verify the NL2SQL agent contract used in Phase 3.

Builds the LangChain SQL agent (SQLDatabaseToolkit + create_agent) with the
configured Qwen3 model and runs a real question against backend/data/app.db.
Prints the agent's tool calls, tool results, and the final answer so the field
names used by the agent loop can be recorded in the phase plan.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.core.llm import build_system_prompt, get_llm

API_KEY = os.environ.get("LLM_API_KEY", "") or os.environ.get(
    "OPENCODE_CODEX_API_KEY", ""
)
MODEL = os.environ.get("LLM_MODEL", "qwen3.7-max")
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")


def redact(value: str) -> str:
    if API_KEY and API_KEY in value:
        return value.replace(API_KEY, "sk-***REDACTED***")
    return value


def main() -> None:
    if not API_KEY:
        print("LLM_API_KEY is not set in backend/.env - refusing to run.")
        sys.exit(2)

    from langchain.agents import create_agent
    from langchain_community.agent_toolkits import SQLDatabaseToolkit
    from langchain_community.utilities import SQLDatabase

    print(f"model={MODEL} | db={DB_URL}")

    llm = get_llm(streaming=False)
    db = SQLDatabase.from_uri(DB_URL)
    print("db.dialect:", db.dialect)
    print("db.get_usable_table_names():", db.get_usable_table_names())

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    print("\ntoolkit tools:", [t.name for t in tools])

    agent = create_agent(
        llm,
        tools,
        system_prompt=build_system_prompt(dialect=db.dialect, top_k=10),
    )

    question = "What are the top 5 products by total quantity sold? List product name and total quantity."
    print("\nquestion:", question)

    stream = agent.stream_events(
        {"messages": [{"role": "user", "content": question}]},
        version="v3",
    )

    steps: list[dict] = []
    final_text_parts: list[str] = []
    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            for token in item.text:
                final_text_parts.append(token)
        elif kind == "tool_calls":
            step = {
                "tool_name": item.tool_name,
                "input": item.input,
                "output_deltas": list(item.output_deltas),
                "output": item.output,
            }
            steps.append(step)
            print(f"\nTool call: {item.tool_name}({redact(str(item.input))})")
            print(f"Tool result: {redact(str(item.output))[:800]}")

    print("\n\nfinal answer:", redact("".join(final_text_parts))[:1500])
    print("\nstep count:", len(steps))


if __name__ == "__main__":
    main()
