"""Configuration management module."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or backend/.env."""

    # Application basics
    app_name: str = "NL2SQLAgent Data Analysis Assistant"
    debug: bool = False
    api_prefix: str = "/api"

    # LLM provider: "openai_compatible" (default, works with OpenCode Go /
    # OpenRouter / DeepSeek / etc.) or "tongyi" (legacy Alibaba Bailian).
    llm_provider: str = "openai_compatible"
    llm_api_key: str = ""
    llm_base_url: str = "https://opencode.ai/zen/go/v1"
    llm_model: str = "qwen3.7-max"

    # Legacy Alibaba Cloud Bailian settings (kept for ChatTongyi compatibility).
    dashscope_api_key: str = ""
    qwen_model: str = "qwen3-max"

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # CORS (supports comma-separated environment variable values)
    # NoDecode: pydantic-settings must not JSON-decode the env value first;
    # the validator below splits the comma-separated string instead.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        """Parse comma-separated CORS_ORIGINS into a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Get the settings singleton."""
    return Settings()
