"""LLM integration: provider-agnostic chat model factory.

The default provider is any OpenAI-compatible endpoint (OpenCode Go, OpenRouter,
DeepSeek, ...) consumed through ``ChatOpenAI``. The legacy ``tongyi`` provider
(``ChatTongyi`` from langchain-community) is kept as a fallback. All provider
choices are configuration-only - the rest of the application never imports a
provider directly.
"""

import os
from functools import lru_cache
from typing import Any

from app.config import Settings, get_settings

# Read-only SQL agent prompt. The agent must never mutate the database and must
# inspect tables/schemas before generating a query.
SQL_AGENT_SYSTEM_PROMPT = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step. Then you should query the schema of the most
relevant tables.

RESPONSE FORMAT
Answer every question as a clear, step-by-step analytical walkthrough. Follow
this exact structure:

1. **Plan** - restate the question in your own words and say what you will
   check (tables, fields, aggregation).
2. **Explore** - after inspecting the tables and schema, briefly describe what
   you found and which fields are relevant to the question.
3. **SQL** - show the query you are about to run, formatted as a code block.
   The SQL you show must be exactly the query you will execute - never
   paraphrase or rewrite it in the answer.
4. **Execute** - state that you are running the query.
5. **Results** - present the exact values returned by the query as a markdown
   table or a numbered list, ordered as requested. Use the real numbers from
   the results; never invent or round values in a misleading way.
6. **Insights** - finish with 2-4 sentences of analysis: highlight the top and
   bottom entries, notable gaps or patterns, and a plausible explanation (for
   example, price versus volume) when the data supports it.

Be thorough but factual: every number you mention must come from the query
results. Answer in the same language the user used for the question.
Formatting: start each numbered section on a new line and put a blank line
before every heading and code block.

Start your answer directly with "1. **Plan**" - never write SQL, code, or any
preamble before section 1. SQL appears only in section 3."""


def build_system_prompt(dialect: str = "sqlite", top_k: int = 10) -> str:
    """Render the read-only SQL agent system prompt with concrete values."""
    return SQL_AGENT_SYSTEM_PROMPT.format(dialect=dialect, top_k=top_k)


def _resolve_api_key(settings: Settings) -> str:
    """Resolve the LLM key: explicit setting, then common env fallbacks."""
    return (
        settings.llm_api_key
        or os.environ.get("OPENCODE_CODEX_API_KEY", "")
        or settings.dashscope_api_key
    ).strip()


def _resolve_model(settings: Settings) -> str:
    """Resolve the model name, preferring the new setting over the legacy one."""
    return settings.llm_model or settings.qwen_model


@lru_cache
def get_llm(streaming: bool = False) -> Any:
    """Create a cached chat model instance for the configured provider.

    Non-streaming instances are used for agent tool-call steps so the complete
    ``tool_calls`` payload is available; streaming instances are used for the
    SSE chat text path.
    """
    settings = get_settings()
    api_key = _resolve_api_key(settings)
    model = _resolve_model(settings)

    if not api_key:
        raise RuntimeError(
            "LLM API key is not configured. Set LLM_API_KEY in backend/.env "
            "(or export OPENCODE_CODEX_API_KEY / DASHSCOPE_API_KEY)."
        )

    if settings.llm_provider == "tongyi":
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=model,
            api_key=api_key,
            temperature=0.7,
            streaming=streaming,
        )

    # Default: OpenAI-compatible endpoint.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=settings.llm_base_url,
        temperature=0.7,
        streaming=streaming,
        max_tokens=2048,
    )
