"""
Pydantic schemas for Project CRUD operations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    """Request payload for creating a new project."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(default="", max_length=1000, description="Optional project description")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Project name cannot be empty or only whitespace")
        return trimmed


class ProjectUpdate(BaseModel):
    """Request payload for updating an existing project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New project name")
    description: Optional[str] = Field(None, max_length=1000, description="New project description")

    @field_validator("name")
    @classmethod
    def validate_name_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Project name cannot be empty or only whitespace")
            return trimmed
        return v


class ProjectResponse(BaseModel):
    """Response payload representing a project."""
    id: str = Field(..., description="Project UUID")
    name: str = Field(..., description="Project name")
    description: str = Field(default="", description="Project description")
    status: str = Field(default="idle", description="Project status (idle, running, done, etc.)")
    document_count: int = Field(default=0, description="Number of uploaded documents")
    requirement_count: int = Field(default=0, description="Number of extracted requirement chunks")
    test_case_count: int = Field(default=0, description="Number of registered test cases")
    test_count: int = Field(default=0, description="Alias for test_case_count")
    bug_count: int = Field(default=0, description="Number of reported bugs")
    run_count: int = Field(default=0, description="Number of execution runs")
    last_run_result: Optional[str] = Field(default=None, description="Result of most recent run if any")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last update timestamp")


class ProjectListResponse(BaseModel):
    """Response payload for listing all projects."""
    projects: List[ProjectResponse] = Field(default_factory=list, description="List of projects")
    total: int = Field(default=0, description="Total number of projects")
