"""
API router for Project CRUD operations.
Prefix: /api/projects
"""

import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.projects import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from backend.app.storage import project_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="Retrieve all projects with aggregate counts of documents, runs, tests, and bugs.",
)
async def list_projects() -> ProjectListResponse:
    projects = project_store.list_projects()
    return ProjectListResponse(
        projects=[ProjectResponse(**p) for p in projects],
        total=len(projects),
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a project and initialize its workspace directory.",
)
async def create_project(payload: ProjectCreate) -> ProjectResponse:
    try:
        project = project_store.create_project(
            name=payload.name,
            description=payload.description,
        )
        return ProjectResponse(**project)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Retrieve detailed metadata and counts for a specific project.",
)
async def get_project(project_id: str) -> ProjectResponse:
    project = project_store.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )
    return ProjectResponse(**project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    description="Update a project's name and/or description.",
)
async def update_project(project_id: str, payload: ProjectUpdate) -> ProjectResponse:
    try:
        updated = project_store.update_project(
            project_id=project_id,
            name=payload.name,
            description=payload.description,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        return ProjectResponse(**updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project, its workspace folder, reports, and all database records.",
)
async def delete_project(project_id: str):
    try:
        success = project_store.delete_project(project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        return None
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
