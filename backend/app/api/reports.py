"""
Reports and Traceability API router for Ojas.

Endpoints:
- GET  /api/projects/{project_id}/reports
- GET  /api/projects/{project_id}/reports/{report_name}
- POST /api/projects/{project_id}/reports/generate
- GET  /api/projects/{project_id}/traceability
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, status

from backend.app.schemas.reports import (
    ReportDetailResponse,
    ReportListResponse,
    ReportSummaryItem,
    TraceabilityCoverageItem,
    TraceabilityResponse,
)
from backend.app.storage.project_store import get_project
from backend.app.storage.report_writer import ReportWriter
from backend.app.storage.traceability import get_coverage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["Reports"])


def _verify_project(project_id: str) -> None:
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )


@router.get(
    "/reports",
    response_model=ReportListResponse,
    summary="List available reports for a project",
)
def list_project_reports(project_id: str) -> ReportListResponse:
    """Return all generated quality, test, and plan reports for the project."""
    _verify_project(project_id)
    writer = ReportWriter(project_id)
    reports = writer.list_reports()
    return ReportListResponse(
        reports=[ReportSummaryItem(**r) for r in reports]
    )


@router.get(
    "/reports/{report_name}",
    summary="Download or view a project report in Markdown or JSON format",
)
def get_project_report(
    project_id: str,
    report_name: str,
    format: str = Query("markdown", description="Output format: 'markdown' or 'json'"),
) -> Response:
    """
    Download or inspect report.
    - format=markdown: returns text/markdown content with download header.
    - format=json: returns structured ReportDetailResponse.
    """
    _verify_project(project_id)
    writer = ReportWriter(project_id)
    clean_name = report_name.replace(".md", "")

    try:
        report_data = writer.get_report_data(clean_name)
    except Exception as exc:
        logger.error("Failed to retrieve report %s for %s: %s", report_name, project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_name}' could not be generated or found.",
        )

    if format.lower() == "json":
        detail = ReportDetailResponse(**report_data)
        return Response(
            content=detail.model_dump_json(),
            media_type="application/json",
            status_code=status.HTTP_200_OK,
        )

    # Return plain markdown
    content = report_data.get("content", "")
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'inline; filename="{clean_name}.md"',
        },
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/reports/generate",
    response_model=ReportDetailResponse,
    summary="Regenerate consolidated report on demand",
)
def generate_project_reports(project_id: str) -> ReportDetailResponse:
    """Regenerate the consolidated report and return details."""
    _verify_project(project_id)
    writer = ReportWriter(project_id)
    writer.generate_consolidated_report()
    data = writer.get_report_data("consolidated_test_report")
    return ReportDetailResponse(**data)


@router.get(
    "/traceability",
    response_model=TraceabilityResponse,
    summary="Get requirement traceability and coverage matrix",
)
def get_project_traceability(project_id: str) -> TraceabilityResponse:
    """Return requirement coverage and traceability matrix for a project."""
    _verify_project(project_id)
    items = get_coverage(project_id)

    total_reqs = len(items)
    covered_by_code = sum(1 for i in items if len(i.get("code_symbols", [])) > 0)
    covered_by_tests = sum(1 for i in items if len(i.get("test_cases", [])) > 0)
    passing_reqs = sum(1 for i in items if i.get("status") == "passing")

    return TraceabilityResponse(
        project_id=project_id,
        coverage=[TraceabilityCoverageItem(**i) for i in items],
        total_requirements=total_reqs,
        covered_by_code=covered_by_code,
        covered_by_tests=covered_by_tests,
        passing_requirements=passing_reqs,
    )
