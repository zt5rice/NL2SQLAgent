"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.database import router as database_router
from app.api.session import router as session_router
from app.config import get_settings
from app.db.connection import ensure_data_dir, init_sample_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: initialize the data directory and sample database on startup."""
    ensure_data_dir()
    init_sample_database()
    print("Application started.")
    yield
    print("Application shutting down.")


# Create the FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Intelligent data analysis assistant - natural language database query system based on LangChain + Qwen3",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(database_router)
app.include_router(session_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service is running"}
