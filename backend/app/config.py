"""配置管理模块。"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量或 backend/.env 读取。"""

    # 应用基础配置
    app_name: str = "NL2SQLAgent Data Analysis Assistant"
    debug: bool = False
    api_prefix: str = "/api"

    # 阿里云百炼配置
    dashscope_api_key: str = ""
    qwen_model: str = "qwen3-max"

    # 数据库配置
    database_url: str = "sqlite:///./data/app.db"

    # CORS 配置（支持逗号分隔的环境变量写法）
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        """将逗号分隔的 CORS_ORIGINS 解析为列表。"""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """获取配置单例。"""
    return Settings()
