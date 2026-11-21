"""
Pydantic schemas for test cases and test execution results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCaseResponse(BaseModel):
    """Schema for a test case."""

    id: str = Field(description="Unique UUID")
    project_id: str = Field(description="Associated project UUID")
    tc_id: str = Field(description="Human-readable ID (e.g. TC-001)")
    name: str = Field(description="Test case name / title")
    file_path: str = Field(description="Path to the test file in workspace")
    function_name: Optional[str] = Field(default=None, description="Test function name")
    linked_req_ids: List[str] = Field(default_factory=list, description="Linked requirement IDs")
    source: str = Field(default="user", description="Source: 'user' or 'generated'")
    status: str = Field(default="not_run", description="Status: 'not_run', 'passed', 'failed', 'error'")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    updated_at: str = Field(description="ISO-8601 update timestamp")


class TestCaseListResponse(BaseModel):
    """Paginated or complete list of test cases."""

    test_cases: List[TestCaseResponse] = Field(default_factory=list)
    total: int = Field(default=0)


class TestResultResponse(BaseModel):
    """Execution result for a single test case within a run."""

    id: str = Field(description="Unique result UUID")
    run_id: str = Field(description="Run UUID")
    test_case_id: str = Field(description="Foreign key to test_cases.id")
    tc_id: str = Field(description="Human-readable ID (e.g. TC-001)")
    iteration: int = Field(default=0, description="Fix loop iteration number")
    result: str = Field(description="Result status: 'passed', 'failed', 'error', 'skipped'")
    duration_ms: Optional[int] = Field(default=None, description="Test duration in ms")
    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    error_message: Optional[str] = Field(default=None, description="Error message / failure trace")
    created_at: str = Field(description="ISO-8601 creation timestamp")


class TestResultsListResponse(BaseModel):
    """List of test execution results."""

    results: List[TestResultResponse] = Field(default_factory=list)
    total: int = Field(default=0)


class TestUploadResponse(BaseModel):
    """Response returned upon uploading test files."""

    message: str = Field(description="Upload and parse status summary")
    file_path: str = Field(description="Path where test file was saved")
    test_cases: List[TestCaseResponse] = Field(default_factory=list)
    total_extracted: int = Field(default=0)
