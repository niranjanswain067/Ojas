"""
Pydantic schemas for Runs, Audit Steps, and Development Plans.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RunCreateRequest(BaseModel):
    """Payload to start a new execution run."""

    run_type: str = Field(
        default="develop",
        description="Type of execution run: 'plan', 'develop', 'test', 'fix_loop'",
    )
    prompt: str = Field(
        default="",
        description="User task prompt or instructions",
    )
    plan_text: Optional[str] = Field(
        default=None,
        description="Optional pre-existing plan text to execute directly",
    )


class RunResponse(BaseModel):
    """Response returned upon submitting a run to the background queue."""

    run_id: str = Field(description="Unique UUID for this run")
    status: str = Field(description="Initial status, usually 'queued' or 'running'")
    message: str = Field(description="Informative message")
    run_type: Optional[str] = Field(default=None, description="Execution run type")


class RunStepResponse(BaseModel):
    """An individual audit step recorded during a run."""

    id: str = Field(description="Step unique UUID")
    run_id: str = Field(description="Associated run UUID")
    step_index: int = Field(description="Order index within the run")
    stage: str = Field(description="Pipeline stage: planning, generating, checking, etc.")
    status: str = Field(description="Step status: started, completed, failed, cancelled")
    message: str = Field(default="", description="Descriptive status message or file path")
    duration_ms: Optional[int] = Field(default=None, description="Step duration in milliseconds")
    created_at: str = Field(description="ISO-8601 creation timestamp")


class RunDetailResponse(BaseModel):
    """Comprehensive details and audit trail of a specific run."""

    id: str = Field(description="Run UUID")
    project_id: str = Field(description="Associated project UUID")
    run_type: str = Field(description="Type of run: plan, develop, test, fix_loop")
    status: str = Field(description="Run status: queued, running, completed, failed, cancelled")
    prompt: str = Field(default="", description="User prompt")
    plan_text: Optional[str] = Field(default=None, description="Generated or executed plan markdown/JSON")
    iteration_count: int = Field(default=0, description="Iterations completed")
    iteration_limit: int = Field(default=5, description="Maximum iterations allowed")
    stop_reason: Optional[str] = Field(default=None, description="Stop condition reason if completed")
    error_message: Optional[str] = Field(default=None, description="Error message if run failed")
    tokens_generated: int = Field(default=0, description="Total tokens generated")
    started_at: Optional[str] = Field(default=None, description="ISO-8601 start timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO-8601 completion timestamp")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    steps: List[RunStepResponse] = Field(default_factory=list, description="Audit steps recorded during run")


class RunListResponse(BaseModel):
    """List of historical runs for a project."""

    runs: List[RunDetailResponse] = Field(default_factory=list, description="Historical run records")
    total: int = Field(description="Total number of runs")


class PlanResponse(BaseModel):
    """Current development plan for a project."""

    project_id: str = Field(description="Associated project UUID")
    plan_text: str = Field(description="Development plan content (markdown or JSON)")
    status: str = Field(
        default="none",
        description="Plan status: 'none', 'pending_approval', 'approved', 'completed'",
    )
    run_id: Optional[str] = Field(default=None, description="Run ID that generated or last updated the plan")
    updated_at: Optional[str] = Field(default=None, description="ISO-8601 timestamp of last update")


class PlanApproveRequest(BaseModel):
    """Payload to review, optionally edit, and approve a plan."""

    plan_text: str = Field(description="Approved (and potentially modified) plan content")
    proceed: bool = Field(default=True, description="Whether to proceed immediately with code generation")


class PlanApproveResponse(BaseModel):
    """Response after approving a plan and queueing code generation."""

    run_id: str = Field(description="Run ID executing development")
    status: str = Field(description="Status of development task: 'queued' or 'approved'")
    message: str = Field(description="Informative message")
