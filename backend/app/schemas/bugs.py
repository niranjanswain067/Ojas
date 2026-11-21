"""
Pydantic schemas for bug reports produced by the Testing Agent.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BugReportResponse(BaseModel):
    """Structured bug report for a failed test."""

    id: str = Field(description="Unique bug UUID")
    project_id: str = Field(description="Associated project UUID")
    run_id: str = Field(description="Associated run UUID")
    bug_id: str = Field(description="Human-readable ID (e.g. B-001)")
    req_id: Optional[str] = Field(default=None, description="Linked requirement ID (e.g. REQ-001)")
    tc_id: Optional[str] = Field(default=None, description="Linked test case ID (e.g. TC-001)")
    file_path: Optional[str] = Field(default=None, description="Failing source file path")
    function_name: Optional[str] = Field(default=None, description="Failing function name")
    severity: str = Field(default="medium", description="Severity: 'critical', 'high', 'medium', 'low'")
    expected_result: str = Field(description="Expected behavior per requirement / assertion")
    actual_result: str = Field(description="Observed behavior or error message")
    probable_cause: Optional[str] = Field(default=None, description="Root cause diagnosed by agent")
    iteration: int = Field(default=0, description="Fix loop iteration number")
    status: str = Field(default="open", description="Status: 'open', 'fixed', 'wont_fix', 'escalated'")
    fix_description: Optional[str] = Field(default=None, description="Summary of fix applied")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    updated_at: str = Field(description="ISO-8601 update timestamp")


class BugListResponse(BaseModel):
    """List of bug reports."""

    bugs: List[BugReportResponse] = Field(default_factory=list)
    total: int = Field(default=0)
