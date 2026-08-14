"""Unit tests for the LLM integration module (no real API calls)."""

from types import SimpleNamespace

import pytest

import app.core.llm as llm_module
from app.core.llm import build_system_prompt, get_llm


@pytest.fixture(autouse=True)
def clear_caches(monkeypatch):
    """Reset lru caches and env so each test starts clean."""
    get_llm.cache_clear()
    llm_module.get_settings.cache_clear()
    monkeypatch.delenv("OPENCODE_CODEX_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    yield
    get_llm.cache_clear()


def _fake_settings(**overrides):
    defaults = {
        "llm_provider": "openai_compatible",
        "llm_api_key": "",
        "llm_base_url": "https://opencode.ai/zen/go/v1",
        "llm_model": "deepseek-v4-flash",
        "dashscope_api_key": "",
        "qwen_model": "qwen3-max",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_system_prompt_is_read_only():
    """The agent prompt forbids write statements and limits result size."""
    prompt = build_system_prompt(dialect="sqlite", top_k=10)
    for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP"]:
        assert forbidden in prompt
    assert "sqlite" in prompt
    assert "top_k" not in prompt  # rendered with the value
    assert "10" in prompt


def test_system_prompt_defines_prose_only_answer_format():
    """The prompt instructs a prose-only 3-section answer without SQL/tables."""
    prompt = build_system_prompt()
    for section in ["1. **Plan**", "2. **Explore**", "3. **Insights**"]:
        assert section in prompt
    assert "Do NOT include SQL, code blocks, or result tables" in prompt


def test_get_llm_raises_without_api_key(monkeypatch):
    """A clear error is raised when no key is configured."""
    monkeypatch.setattr(llm_module, "get_settings", lambda: _fake_settings(llm_api_key=""))
    with pytest.raises(RuntimeError, match="LLM API key is not configured"):
        get_llm(streaming=False)


def test_get_llm_falls_back_to_env_key(monkeypatch):
    """OPENCODE_CODEX_API_KEY is accepted when LLM_API_KEY is empty."""
    monkeypatch.setenv("OPENCODE_CODEX_API_KEY", "sk-opencode-test")
    monkeypatch.setattr(llm_module, "get_settings", lambda: _fake_settings(llm_api_key=""))
    llm = get_llm(streaming=False)
    assert llm.model_name == "deepseek-v4-flash"
    assert llm.openai_api_base == "https://opencode.ai/zen/go/v1"
    assert llm.openai_api_key.get_secret_value() == "sk-opencode-test"


def test_get_llm_returns_chatopenai_for_default_provider(monkeypatch):
    """The default provider maps to ChatOpenAI with the configured endpoint."""
    monkeypatch.setattr(
        llm_module,
        "get_settings",
        lambda: _fake_settings(
            llm_api_key="sk-test",
            llm_base_url="https://example.com/v1",
            llm_model="deepseek-v4-flash",
        ),
    )
    llm = get_llm(streaming=False)
    assert type(llm).__name__ == "ChatOpenAI"
    assert llm.openai_api_base == "https://example.com/v1"
    assert llm.model_name == "deepseek-v4-flash"


def test_get_llm_tongyi_provider_uses_legacy_class(monkeypatch):
    """LLM_PROVIDER=tongyi maps to ChatTongyi (legacy Bailian fallback)."""
    monkeypatch.setattr(
        llm_module,
        "get_settings",
        lambda: _fake_settings(llm_provider="tongyi", dashscope_api_key="sk-test"),
    )
    llm = get_llm(streaming=False)
    assert type(llm).__name__ == "ChatTongyi"
