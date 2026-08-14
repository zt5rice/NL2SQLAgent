"""Sliding-window conversation memory per session.

History is rebuilt from ``chat_messages`` (persistence of truth) and cached in
memory. New messages must call :func:`invalidate` so the next read rebuilds.
"""

from functools import lru_cache
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.db import session_store

DEFAULT_MAX_ROUNDS = 10


def sliding_window(
    messages: list[dict], max_rounds: int = DEFAULT_MAX_ROUNDS
) -> list[dict]:
    """Keep the last ``max_rounds`` user/assistant rounds (2x messages).

    The window is aligned to start on a user message when possible so the model
    never sees a truncated assistant reply as the first turn.
    """
    size = max_rounds * 2
    window = messages[-size:]
    while len(window) > 1 and window[0].get("role") != "user":
        window.pop(0)
    return window


def to_langchain_messages(messages: list[dict]) -> list[BaseMessage]:
    """Convert persisted message dicts into LangChain message objects."""
    converted: list[BaseMessage] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        elif role == "system":
            converted.append(SystemMessage(content=content))
        # Unknown roles are skipped so a bad row can never crash the chat flow.
    return converted


@lru_cache(maxsize=256)
def _cached_history(session_id: str) -> tuple[BaseMessage, ...]:
    """Cached LangChain message list for a session (immutable tuple for cache)."""
    rows = session_store.list_messages(session_id)
    window = sliding_window(rows)
    return tuple(to_langchain_messages(window))


def get_history_messages(session_id: str) -> list[BaseMessage]:
    """Recent LangChain messages for a session (cached)."""
    return list(_cached_history(session_id))


def invalidate(session_id: str | None = None) -> None:
    """Drop cached history. Pass a session id to scope, or none to clear all."""
    if session_id is None:
        _cached_history.cache_clear()
        return
    # lru_cache has no per-key removal; clear the small cache and rebuild lazily.
    _cached_history.cache_clear()


def append_turn(session_id: str, user_content: str, assistant_content: str) -> None:
    """Persist one user/assistant round and invalidate the memory cache."""
    session_store.add_message(session_id, "user", user_content)
    session_store.add_message(session_id, "assistant", assistant_content)
    invalidate(session_id)
