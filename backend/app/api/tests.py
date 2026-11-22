"""
API router for test cases and test execution results.
Supports test file upload, AST registration, and result retrieval.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas.tests import (
    TestCaseListResponse,
    TestCaseResponse,
    TestResultResponse,
    TestResultsListResponse,
    TestUploadResponse,
)
from backend.app.storage.document_store import ensure_project
from backend.app.storage.file_store import write_file
from backend.app.storage.test_store import (
    get_latest_test_results,
    get_test_cases,
    get_test_results,
    register_test_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tests"])


@router.post(
    "/api/projects/{project_id}/tests",
    response_model=TestUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and register pytest test file",
)
async def upload_test_file(
    project_id: str,
    file: UploadFile = File(...),
) -> TestUploadResponse:
    """
    Upload a pytest test file (.py) to workspace/<project_id>/tests/,
    parse with AST to extract test cases, and register in database.
    """
    ensure_project(project_id)
    filename = file.filename or "test_suite.py"
    if not filename.endswith(".py"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Python test files (.py) are supported.",
        )

    try:
        content_bytes = await file.read()
        code = content_bytes.decode("utf-8")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        )

    # Save to workspace/tests/
    target_path = f"tests/{filename}"
    try:
        write_file(project_id, target_path, code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to project workspace: {exc}",
        )

    # Register in test_cases table
    records = register_test_file(project_id, target_path, code, source="user")
    tc_responses = [TestCaseResponse(**r) for r in records]

    return TestUploadResponse(
        message=f"Successfully uploaded and parsed {len(tc_responses)} test case(s).",
        file_path=target_path,
        test_cases=tc_responses,
        total_extracted=len(tc_responses),
    )


@router.get(
    "/api/projects/{project_id}/tests",
    response_model=TestCaseListResponse,
    summary="List all test cases for a project",
)
def list_project_test_cases(project_id: str) -> TestCaseListResponse:
    """
    Retrieve all registered test cases for a project.
    """
    ensure_project(project_id)
    records = get_test_cases(project_id)
    items = [TestCaseResponse(**r) for r in records]
    return TestCaseListResponse(test_cases=items, total=len(items))


@router.get(
    "/api/projects/{project_id}/tests/results",
    response_model=TestResultsListResponse,
    summary="Get recent test results for a project",
)
def list_project_test_results(project_id: str) -> TestResultsListResponse:
    """
    Retrieve latest test execution results for a project.
    """
    ensure_project(project_id)
    records = get_latest_test_results(project_id)
    items = [TestResultResponse(**r) for r in records]
    return TestResultsListResponse(results=items, total=len(items))


@router.get(
    "/api/runs/{run_id}/test-results",
    response_model=TestResultsListResponse,
    summary="Get test results for a specific run",
)
def get_run_test_results(run_id: str) -> TestResultsListResponse:
    """
    Retrieve test execution results produced by a specific run.
    """
    records = get_test_results(run_id)
    items = [TestResultResponse(**r) for r in records]
    return TestResultsListResponse(results=items, total=len(items))
