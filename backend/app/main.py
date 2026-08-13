"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（数据库初始化将在 Phase 1 的 SQLite 任务中接入）。"""
    print("Application started.")
    yield
    print("Application shutting down.")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="智能数据分析助理 - 基于 LangChain + Qwen3 的自然语言数据库查询系统",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查接口。"""
    return {"status": "ok", "message": "Service is running"}
