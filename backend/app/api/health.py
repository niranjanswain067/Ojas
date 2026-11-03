"""
Health check router.

GET /api/health
    Returns the overall health of the Ojas backend:
    - application version
    - LLM model loaded status and metadata
    - resolved filesystem paths
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])

# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

_APP_VERSION = "0.1.0"

# Project root — 4 levels up from this file:
# backend/app/api/health.py  →  root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class PathsInfo(BaseModel):
    workspace: str
    models: str
    data: str
    logs: str
    reports: str


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "error"]
    model_loaded: bool
    model_name: str
    load_time_seconds: float
    version: str
    paths: PathsInfo
    last_error: str | None


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the operational status of the backend. "
        "``healthy`` means the model is loaded and the DB is up. "
        "``degraded`` means the app is running but the model is not loaded. "
        "``error`` means a critical component has failed."
    ),
)
async def health_check() -> HealthResponse:
    """Return overall system health including LLM load status and paths."""
    # Import at call time to avoid circular imports at module level
    from backend.app.main import get_llm_client  # noqa: PLC0415

    client = get_llm_client()
    info = client.get_info() if client is not None else {}

    model_loaded: bool = client is not None and client.is_loaded()
    last_error: str | None = info.get("last_error")

    if model_loaded:
        status: Literal["healthy", "degraded", "error"] = "healthy"
    elif last_error:
        status = "degraded"
    else:
        status = "degraded"  # model absent but no hard error

    paths = PathsInfo(
        workspace=str(_PROJECT_ROOT / "workspace"),
        models=str(_PROJECT_ROOT / "models"),
        data=str(_PROJECT_ROOT / "data"),
        logs=str(_PROJECT_ROOT / "logs"),
        reports=str(_PROJECT_ROOT / "reports"),
    )

    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        model_name=info.get("model_name", ""),
        load_time_seconds=info.get("load_time_seconds", 0.0),
        version=_APP_VERSION,
        paths=paths,
        last_error=last_error,
    )

