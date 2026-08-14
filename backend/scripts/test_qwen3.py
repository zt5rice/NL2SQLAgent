"""Scratch test: verify the Qwen3 integration contract used in Phase 3.

Tests, with the real key from backend/.env against the configured provider
(default: OpenCode Go, OpenAI-compatible endpoint):
  1. Non-streaming invoke - full AIMessage fields
  2. Streaming - chunk fields
  3. bind_tools - tool-call round trip (fields used by the agent loop)

This file is scratch/diagnostic only and is not part of the application.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Load backend/.env so LLM_* settings are available.
load_dotenv(BACKEND_ROOT / ".env")

from app.core.llm import get_llm

API_KEY = os.environ.get("LLM_API_KEY", "") or os.environ.get(
    "OPENCODE_CODEX_API_KEY", ""
)
MODEL = os.environ.get("LLM_MODEL", "qwen3.7-max")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://opencode.ai/zen/go/v1")


def redact(value: str) -> str:
    """Never leak the API key into printed output."""
    if API_KEY and API_KEY in value:
        return value.replace(API_KEY, "sk-***REDACTED***")
    return value


def dump(name: str, obj) -> None:
    text = redact(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    print(f"\n===== {name} =====")
    print(text[:6000])


def message_to_dict(msg) -> dict:
    d = {
        "type": type(msg).__name__,
        "content": msg.content,
    }
    if getattr(msg, "tool_calls", None):
        d["tool_calls"] = [
            {
                "id": tc.get("id"),
                "name": tc.get("name"),
                "args": tc.get("args"),
                "type": tc.get("type"),
            }
            for tc in msg.tool_calls
        ]
    if getattr(msg, "additional_kwargs", None):
        d["additional_kwargs"] = {
            k: v
            for k, v in msg.additional_kwargs.items()
            if k not in ("reasoning_content",) or v
        }
    if getattr(msg, "response_metadata", None):
        d["response_metadata"] = msg.response_metadata
    return d


def test_llm_contract() -> None:
    llm = get_llm(streaming=False)
    messages = [
        ("system", "You are a concise data assistant. Answer in English."),
        ("human", "Which table stores product sales? Reply in one short sentence."),
    ]

    # 1. Non-streaming invoke: capture the full AIMessage structure.
    print("\n### 1. Non-streaming invoke")
    resp = llm.invoke(messages)
    dump("AIMessage (non-streaming)", message_to_dict(resp))

    # 2. Streaming: capture chunk fields (content deltas + metadata).
    print("\n### 2. Streaming")
    chunks: list[dict] = []
    for chunk in llm.stream(messages):
        chunks.append(
            {
                "content": chunk.content,
                "additional_kwargs": chunk.additional_kwargs,
                "response_metadata": chunk.response_metadata,
            }
        )
    dump(f"stream chunks (n={len(chunks)})", chunks[:12])
    print("stream total text:", redact("".join(c["content"] for c in chunks))[:500])

    # 3. Tool calling: define tools, bind, and inspect tool_calls + round trip.
    print("\n### 3. bind_tools tool-call round trip")
    from langchain_core.messages import ToolMessage
    from pydantic import BaseModel, Field

    class TopProducts(BaseModel):
        """Get the top N products by total quantity sold."""

        n: int = Field(..., description="Number of products to return, e.g. 5")

    class SalesByCategory(BaseModel):
        """Get total quantity sold grouped by product category."""

        category: str = Field(..., description="Exact category name to filter on")

    model_with_tools = llm.bind_tools([TopProducts, SalesByCategory])
    tool_ai = model_with_tools.invoke(
        [
            (
                "system",
                "You can call tools to query the sales database. Call the tool whose "
                "name is 'TopProducts' with n=3 when asked for top products.",
            ),
            ("human", "What are the top 3 products by quantity sold?"),
        ]
    )
    dump("AIMessage with tool_calls", message_to_dict(tool_ai))

    # Round trip: feed a fake ToolMessage back and verify the follow-up fields.
    tool_call = tool_ai.tool_calls[0]
    follow_up = model_with_tools.invoke(
        [
            ("system", "You can call tools to query the sales database."),
            ("human", "What are the top 3 products by quantity sold?"),
            tool_ai,
            ToolMessage(
                content='[{"product_name": "Wireless Mouse", "total_quantity": 120}]',
                tool_call_id=tool_call["id"],
            ),
        ]
    )
    dump("AIMessage after tool result", message_to_dict(follow_up))


def main() -> None:
    if not API_KEY:
        print("LLM_API_KEY is not set in backend/.env - refusing to run.")
        sys.exit(2)
    print(f"provider=openai_compatible | base_url={BASE_URL} | model={MODEL}")
    test_llm_contract()
    print("\nDone.")


if __name__ == "__main__":
    main()
