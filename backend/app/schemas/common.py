"""
Common Pydantic response schemas shared across all Ojas API routers.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """
    Returned by exception handlers for any 4xx / 5xx error.

    Attributes
    ----------
    status_code : int   HTTP status code (e.g. 404, 422, 500).
    detail      : str   Human-readable error description.
    timestamp   : str   ISO 8601 UTC timestamp of when the error occurred.
    """

    status_code: int = Field(..., examples=[404])
    detail: str = Field(..., examples=["Project not found"])
    timestamp: str = Field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# Success response
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel):
    """
    Generic success acknowledgement for operations that have no specific
    return value (e.g. DELETE endpoints).

    Attributes
    ----------
    status  : str   Always ``"ok"``.
    message : str   Human-readable description of what happened.
    """

    status: str = Field(default="ok", examples=["ok"])
    message: str = Field(..., examples=["Project deleted successfully"])

