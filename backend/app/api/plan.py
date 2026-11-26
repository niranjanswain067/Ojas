"""
API router for development plans: retrieving current plan, editing, and approving.
"""

import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from backend.app.orchestrator import Orchestrator

try:
    from backend.app.rag.search import SearchEngine
except ImportError:
    SearchEngine = None  # type: ignore
from backend.app.schemas.runs import (
    PlanApproveRequest,
    PlanApproveResponse,
    PlanResponse,
)
from backend.app.storage.document_store import ensure_project
from backend.app.storage.run_store import (
    get_latest_plan,
    get_run,
    save_run,
    update_plan_approval,
)
from backend.app.tasks.task_manager import get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/plan", tags=["plan"])


@router.get(
    "",
    response_model=PlanResponse,
    summary="Get the current development plan for a project",
)
def get_project_plan(project_id: str) -> PlanResponse:
    """
    Retrieve the most recently generated development plan for project_id.
    Returns 404 if no plan has been generated yet.
    """
    ensure_project(project_id)
    latest = get_latest_plan(project_id)
    if not latest or not latest.get("plan_text"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No development plan has been generated for this project yet.",
        )

    return PlanResponse(
        project_id=project_id,
        plan_text=latest["plan_text"],
        status=latest.get("status") or "pending_approval",
        run_id=latest["id"],
        updated_at=latest.get("completed_at") or latest.get("created_at"),
    )


@router.post(
    "/approve",
    response_model=PlanApproveResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Approve the development plan and trigger code generation",
)
def approve_project_plan(project_id: str, req: PlanApproveRequest) -> PlanApproveResponse:
    """
    Approve the development plan (optionally with user edits) and proceed
    to autonomous file-by-file code generation.
    """
    ensure_project(project_id)
    task_mgr = get_task_manager()

    # Save approved plan in database
    update_plan_approval(project_id, req.plan_text)

    if not req.proceed:
        return PlanApproveResponse(
            run_id="",
            status="approved",
            message="Plan saved and approved successfully.",
        )

    # Brief grace period: if the plan-generation task just finished, the
    # background thread may still be unwinding. Wait up to 3 s for it to
    # release the TaskManager lock before checking busy status.
    if task_mgr.is_busy():
        for _ in range(6):  # 6 × 0.5 s = 3 s max
            time.sleep(0.5)
            if not task_mgr.is_busy():
                break

    if task_mgr.is_busy():
        current_id = task_mgr.get_current_run_id()
        if current_id:
            curr_run = get_run(current_id)
            if curr_run and curr_run.get("status") in ("pending_approval", "completed", "cancelled", "failed"):
                logger.info(
                    "Task %s is in status '%s'; clearing TaskManager busy lock to allow development run.",
                    current_id,
                    curr_run.get("status"),
                )
                task_mgr.clear_current()

    if task_mgr.is_busy():
        current_id = task_mgr.get_current_run_id()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Another task ({current_id}) is currently executing. Cannot start development run.",
        )

    run_id = str(uuid.uuid4())
    save_run(
        project_id=project_id,
        run_type="develop",
        prompt="Develop from approved plan",
        plan_text=req.plan_text,
        status="queued",
        run_id=run_id,
    )

    search_eng = None
    if SearchEngine is not None:
        try:
            search_eng = SearchEngine(project_id=project_id)
        except Exception as exc:
            logger.warning("SearchEngine init failed: %s", exc)
    orchestrator = Orchestrator(search_engine=search_eng)

    def worker_fn() -> None:
        try:
            orchestrator.run_develop(
                project_id=project_id,
                prompt="Develop from approved plan",
                plan_text=req.plan_text,
                run_id=run_id,
            )
        except Exception as exc:
            logger.exception("Error in approved plan worker (run %s): %s", run_id, exc)

    submitted = task_mgr.submit(worker_fn, run_id=run_id)
    if not submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TaskManager rejected task submission.",
        )

    return PlanApproveResponse(
        run_id=run_id,
        status="queued",
        message="Development plan approved. Code generation started in the background.",
    )
