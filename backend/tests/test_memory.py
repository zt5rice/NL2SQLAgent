"""Tests for the sliding-window context memory."""

import uuid

from langchain_core.messages import AIMessage, HumanMessage

from app.core import memory
from app.db import session_store


def _new_session() -> str:
    return session_store.create_session()["id"]


def _seed_messages(session_id: str, count: int) -> None:
    """Add ``count`` user/assistant turns (2*count messages)."""
    for i in range(count):
        session_store.add_message(session_id, "user", f"question {i}")
        session_store.add_message(session_id, "assistant", f"answer {i}")


def test_sliding_window_keeps_last_10_rounds():
    """Only the most recent 10 rounds (20 messages) survive the window."""
    session_id = _new_session()
    try:
        _seed_messages(session_id, 15)  # 30 messages total
        history = memory.get_history_messages(session_id)
        assert len(history) == 20
        assert isinstance(history[0], HumanMessage)
        assert history[0].content == "question 5"  # first kept user message
        assert history[-1].content == "answer 14"
    finally:
        session_store.delete_session(session_id)
        memory.invalidate()


def test_sliding_window_aligns_to_user_message():
    """The window drops a half assistant prefix so it starts on a user message."""
    session_id = _new_session()
    try:
        _seed_messages(session_id, 10)
        session_store.add_message(session_id, "assistant", "orphan reply")
        history = memory.get_history_messages(session_id)
        assert len(history) == 19  # 21 messages, leading half-turn dropped
        assert isinstance(history[0], HumanMessage)
        assert history[0].content == "question 1"
        assert history[-1].content == "orphan reply"
    finally:
        session_store.delete_session(session_id)
        memory.invalidate()


def test_role_conversion():
    """user/assistant roles become HumanMessage/AIMessage objects."""
    session_id = _new_session()
    try:
        session_store.add_message(session_id, "user", "hello")
        session_store.add_message(session_id, "assistant", "hi")
        history = memory.get_history_messages(session_id)
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)
        assert history[1].content == "hi"
    finally:
        session_store.delete_session(session_id)
        memory.invalidate()


def test_append_turn_persists_and_invalidates_cache():
    """append_turn writes a round and the next read sees it."""
    session_id = _new_session()
    try:
        memory.append_turn(session_id, "q1", "a1")
        first = memory.get_history_messages(session_id)
        assert len(first) == 2

        memory.append_turn(session_id, "q2", "a2")
        second = memory.get_history_messages(session_id)
        assert [m.content for m in second] == ["q1", "a1", "q2", "a2"]
    finally:
        session_store.delete_session(session_id)
        memory.invalidate()


def test_empty_session_returns_empty_history():
    """A session with no messages yields an empty history (no crash)."""
    session_id = _new_session()
    try:
        assert memory.get_history_messages(session_id) == []
    finally:
        session_store.delete_session(session_id)
        memory.invalidate()
