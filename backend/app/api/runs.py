"""
API router for execution runs: starting runs, listing history, and retrieving run details.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from backend.app.orchestrator import Orchestrator

try:
    from backend.app.rag.search import SearchEngine
except ImportError:
    SearchEngine = None  # type: ignore
from backend.app.schemas.runs import (
    RunCreateRequest,
    RunDetailResponse,
    RunListResponse,
    RunResponse,
    RunStepResponse,
)
from backend.app.storage.document_store import ensure_project
from backend.app.storage.run_store import get_run, get_run_history, save_run
from backend.app.tasks.task_manager import get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["runs"])


def _build_orchestrator(project_id: str) -> Orchestrator:
    """Build an orchestrator instance configured for project_id."""
    search_eng = None
    if SearchEngine is not None:
        try:
            search_eng = SearchEngine(project_id=project_id)
        except Exception as exc:
            logger.warning("SearchEngine init failed: %s", exc)
    return Orchestrator(search_engine=search_eng)


@router.post(
    "/api/projects/{project_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new execution run",
)
def start_project_run(project_id: str, req: RunCreateRequest) -> RunResponse:
    """
    Submit a task (plan, develop, etc.) to the background TaskManager.
    Returns HTTP 409 Conflict if another background task is already executing.
    """
    ensure_project(project_id)
    task_mgr = get_task_manager()

    if task_mgr.is_busy():
        current_id = task_mgr.get_current_run_id()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Another background run ({current_id}) is currently in progress. Only one task can execute at a time.",
        )

    run_id = str(uuid.uuid4())

    # Save initial run record in database
    save_run(
        project_id=project_id,
        run_type=req.run_type,
        prompt=req.prompt,
        plan_text=req.plan_text,
        status="queued",
        run_id=run_id,
    )

    # Worker dispatch
    orchestrator = _build_orchestrator(project_id)

    def worker_fn() -> None:
        try:
            if req.run_type == "plan":
                orchestrator.run_plan(project_id, prompt=req.prompt, run_id=run_id)
            elif req.run_type == "test":
                orchestrator.run_test(project_id, run_id=run_id)
            elif req.run_type == "fix_loop":
                orchestrator.run_fix_loop(project_id, run_id=run_id)
            else:
                orchestrator.run_develop(
                    project_id,
                    prompt=req.prompt,
                    plan_text=req.plan_text,
                    run_id=run_id,
                )
        except Exception as exc:
            logger.exception("Worker execution error in run %s: %s", run_id, exc)

    submitted = task_mgr.submit(worker_fn, run_id=run_id)
    if not submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to queue task: TaskManager rejected submission.",
        )

    return RunResponse(
        run_id=run_id,
        status="queued",
        message=f"{req.run_type.capitalize()} run queued successfully.",
        run_type=req.run_type,
    )


@router.get(
    "/api/projects/{project_id}/runs",
    response_model=RunListResponse,
    summary="List run history for a project",
)
def list_project_runs(project_id: str, limit: int = 50) -> RunListResponse:
    """
    Retrieve historical execution runs for the specified project.
    """
    ensure_project(project_id)
    history = get_run_history(project_id, limit=limit)
    items = []
    for r in history:
        steps = [RunStepResponse(**s) for s in r.get("steps", [])]
        items.append(
            RunDetailResponse(
                id=r["id"],
                project_id=r["project_id"],
                run_type=r["run_type"],
                status=r["status"],
                prompt=r.get("prompt") or "",
                plan_text=r.get("plan_text"),
                iteration_count=r.get("iteration_count") or 0,
                iteration_limit=r.get("iteration_limit") or 5,
                stop_reason=r.get("stop_reason"),
                error_message=r.get("error_message"),
                tokens_generated=r.get("tokens_generated") or 0,
                started_at=r.get("started_at"),
                completed_at=r.get("completed_at"),
                created_at=r["created_at"],
                steps=steps,
            )
        )
    return RunListResponse(runs=items, total=len(items))


@router.get(
    "/api/runs/{run_id}",
    response_model=RunDetailResponse,
    summary="Get details of a specific run",
)
def get_run_detail(run_id: str) -> RunDetailResponse:
    """
    Retrieve full execution details, status, and audit steps for a run.
    """
    data = get_run(run_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )

    steps = [RunStepResponse(**s) for s in data.get("steps", [])]
    return RunDetailResponse(
        id=data["id"],
        project_id=data["project_id"],
        run_type=data["run_type"],
        status=data["status"],
        prompt=data.get("prompt") or "",
        plan_text=data.get("plan_text"),
        iteration_count=data.get("iteration_count") or 0,
        iteration_limit=data.get("iteration_limit") or 5,
        stop_reason=data.get("stop_reason"),
        error_message=data.get("error_message"),
        tokens_generated=data.get("tokens_generated") or 0,
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        created_at=data["created_at"],
        steps=steps,
    )
