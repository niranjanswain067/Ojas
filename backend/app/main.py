"""
Ojas FastAPI application entry point.

Startup sequence
----------------
1. Load settings (Pydantic / JSON).
2. Create data/ directory.
3. Initialise SQLite database (idempotent).
4. Load the LLM model (non-fatal if missing).
5. Mount API routers.
6. Serve the built frontend from frontend/dist/ (if it exists).

Run with:
    uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings
from backend.app.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)

# Project root — 3 levels up from this file: backend/app/main.py → root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Global LLM client holder
# ---------------------------------------------------------------------------

_llm_client = None  # set during startup


def get_llm_client():
    """Return the global LLM client instance (may be None if not loaded)."""
    return _llm_client


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _configure_logging(log_level: str) -> None:
    level = log_level.upper()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": str(_PROJECT_ROOT / "logs" / "ojas.log"),
                    "formatter": "default",
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": level,
            },
        }
    )


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """FastAPI lifespan: runs startup code, then yields, then shutdown."""
    global _llm_client

    settings = get_settings()
    _configure_logging(settings.log_level)

    logger.info("=" * 60)
    logger.info("Ojas backend starting up")
    logger.info("Project root : %s", _PROJECT_ROOT)
    logger.info("=" * 60)

    # ── 1. Create required directories ────────────────────────────────
    for folder in ("data", "logs", "workspace", "reports"):
        (_PROJECT_ROOT / folder).mkdir(parents=True, exist_ok=True)

    # ── 2. Initialise SQLite database ─────────────────────────────────
    try:
        from backend.app.storage.db import init_database
        init_database()
        logger.info("Database initialised successfully.")
    except Exception:
        logger.exception("Database initialisation failed — continuing anyway.")

    # ── 3. Load LLM model (non-fatal) ─────────────────────────────────
    try:
        from backend.app.llm.llama_cpp_client import LlamaCppClient
        logger.info("Loading LLM model …")
        _llm_client = LlamaCppClient()
        if _llm_client.is_loaded():
            info = _llm_client.get_info()
            logger.info(
                "Model ready: %s  (loaded in %.2f s)",
                info["model_name"],
                info["load_time_seconds"],
            )
        else:
            logger.warning(
                "Model NOT loaded: %s",
                _llm_client.get_info().get("last_error"),
            )
    except Exception:
        logger.exception("Unexpected error while loading LLM — running without model.")
        _llm_client = None

    logger.info("Startup complete. Serving on http://%s:%d", settings.host, settings.port)

    yield  # ← app is now running

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("Ojas backend shutting down.")
    _llm_client = None


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ojas",
    version="0.1.0",
    description=(
        "Ojas — offline AI-powered software development assistant. "
        "Reads requirement documents, generates Python code, runs pytest, "
        "and iterates a fix loop — all without internet access."
    ),
    lifespan=_lifespan,
    # Disable the default CDN-backed docs (they break offline).
    # Swap to offline docs in Phase 19 if needed.
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow Vite dev server (localhost:5173) during development
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            status_code=404,
            detail=str(getattr(exc, "detail", "Resource not found")),
        ).model_dump(),
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            status_code=422,
            detail="Request validation failed. Check the request body and parameters.",
        ).model_dump(),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc) -> JSONResponse:
    logger.exception("Unhandled server error for %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status_code=500,
            detail="An internal server error occurred.",
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------

from backend.app.api.health import router as health_router  # noqa: E402

app.include_router(health_router)

# Future routers will be added here (projects, files, settings, runs …)

# ---------------------------------------------------------------------------
# Serve built frontend (if it exists)
# ---------------------------------------------------------------------------

_frontend_dist = _PROJECT_ROOT / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    logger.info("Serving frontend from %s", _frontend_dist)

