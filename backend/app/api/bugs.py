"""
API router for bug reports generated during test failure analysis and fix loops.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.schemas.bugs import BugListResponse, BugReportResponse
from backend.app.storage.bug_store import (
    get_bug_report,
    get_bug_reports,
    update_bug_report_status,
)
from backend.app.storage.document_store import ensure_project

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bugs"])


class BugStatusUpdateRequest(BaseModel):
    """Payload to update bug report status."""

    status: str = Field(description="New status: 'open', 'fixed', 'wont_fix', 'escalated'")
    fix_description: Optional[str] = Field(default=None, description="Optional description of fix")


@router.get(
    "/api/projects/{project_id}/bugs",
    response_model=BugListResponse,
    summary="List bug reports for a project",
)
def list_project_bugs(
    project_id: str,
    run_id: Optional[str] = None,
    status: Optional[str] = None,
) -> BugListResponse:
    """
    Retrieve all bug reports for a project, optionally filtered by run_id or status.
    """
    ensure_project(project_id)
    records = get_bug_reports(project_id, run_id=run_id, status=status)
    items = [BugReportResponse(**r) for r in records]
    return BugListResponse(bugs=items, total=len(items))


@router.get(
    "/api/bugs/{bug_id}",
    response_model=BugReportResponse,
    summary="Get single bug report detail",
)
def get_single_bug(bug_id: str) -> BugReportResponse:
    """
    Retrieve full details for a bug report by ID or human-readable bug_id.
    """
    record = get_bug_report(bug_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug report '{bug_id}' not found.",
        )
    return BugReportResponse(**record)


@router.patch(
    "/api/bugs/{bug_id}",
    response_model=BugReportResponse,
    summary="Update bug report status",
)
def update_bug_status(bug_id: str, req: BugStatusUpdateRequest) -> BugReportResponse:
    """
    Update status and optional fix description for a bug report.
    """
    record = get_bug_report(bug_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug report '{bug_id}' not found.",
        )
    update_bug_report_status(bug_id, req.status, fix_description=req.fix_description)
    updated = get_bug_report(bug_id)
    return BugReportResponse(**updated)  # type: ignore
