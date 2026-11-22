"""
Database store for execution runs and audit steps (runs and run_steps tables).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.storage.db import execute_query, fetch_all, fetch_one
from backend.app.storage.document_store import ensure_project

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def save_run(
    project_id: str,
    run_type: str,
    prompt: str = "",
    plan_text: Optional[str] = None,
    iteration_limit: int = 5,
    status: str = "queued",
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert a new execution run record into the runs table.
    """
    ensure_project(project_id)
    r_id = run_id or str(uuid.uuid4())
    now = _now_iso()

    execute_query(
        """
        INSERT INTO runs (
            id, project_id, run_type, status, prompt, plan_text,
            iteration_count, iteration_limit, stop_reason, error_message,
            tokens_generated, started_at, completed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL, NULL, 0, NULL, NULL, ?)
        """,
        (
            r_id,
            project_id,
            run_type,
            status,
            prompt,
            plan_text,
            iteration_limit,
            now,
        ),
    )

    return get_run(r_id) or {
        "id": r_id,
        "project_id": project_id,
        "run_type": run_type,
        "status": status,
        "prompt": prompt,
        "plan_text": plan_text,
        "iteration_count": 0,
        "iteration_limit": iteration_limit,
        "tokens_generated": 0,
        "created_at": now,
        "steps": [],
    }


def update_run(
    run_id: str,
    status: Optional[str] = None,
    plan_text: Optional[str] = None,
    iteration_count: Optional[int] = None,
    stop_reason: Optional[str] = None,
    error_message: Optional[str] = None,
    tokens_generated: Optional[int] = None,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update specific columns of an existing run record.
    """
    fields = []
    values = []

    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if plan_text is not None:
        fields.append("plan_text = ?")
        values.append(plan_text)
    if iteration_count is not None:
        fields.append("iteration_count = ?")
        values.append(iteration_count)
    if stop_reason is not None:
        fields.append("stop_reason = ?")
        values.append(stop_reason)
    if error_message is not None:
        fields.append("error_message = ?")
        values.append(error_message)
    if tokens_generated is not None:
        fields.append("tokens_generated = ?")
        values.append(tokens_generated)
    if started_at is not None:
        fields.append("started_at = ?")
        values.append(started_at)
    if completed_at is not None:
        fields.append("completed_at = ?")
        values.append(completed_at)

    if not fields:
        return get_run(run_id)

    values.append(run_id)
    sql = f"UPDATE runs SET {', '.join(fields)} WHERE id = ?"
    execute_query(sql, tuple(values))

    return get_run(run_id)


def save_run_step(
    run_id: str,
    step_index: int,
    stage: str,
    status: str,
    message: str = "",
    duration_ms: Optional[int] = None,
    step_id: Optional[str] = None,
    agent: Optional[str] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record an individual execution or audit step in run_steps.
    """
    s_id = step_id or str(uuid.uuid4())
    now = _now_iso()

    execute_query(
        """
        INSERT INTO run_steps (
            id, run_id, step_index, stage, agent, description, file_path, status, duration_ms, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (s_id, run_id, step_index, stage, agent, message, file_path, status, duration_ms, now),
    )

    return {
        "id": s_id,
        "run_id": run_id,
        "step_index": step_index,
        "stage": stage,
        "status": status,
        "message": message,
        "description": message,
        "duration_ms": duration_ms,
        "created_at": now,
    }


def get_run_steps(run_id: str) -> List[Dict[str, Any]]:
    """Return all audit steps for a run ordered by step_index ASC."""
    rows = fetch_all(
        "SELECT * FROM run_steps WHERE run_id = ? ORDER BY step_index ASC, created_at ASC",
        (run_id,),
    )
    result = []
    for r in rows:
        d = dict(r)
        if "description" in d and "message" not in d:
            d["message"] = d["description"]
        result.append(d)
    return result


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single run by ID including its recorded audit steps.
    """
    row = fetch_one("SELECT * FROM runs WHERE id = ?", (run_id,))
    if row is None:
        return None
    data = dict(row)
    data["steps"] = get_run_steps(run_id)
    return data


def get_run_history(project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch all runs for a project ordered by created_at DESC.
    """
    rows = fetch_all(
        "SELECT * FROM runs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
        (project_id, limit),
    )
    results = []
    for r in rows:
        d = dict(r)
        d["steps"] = get_run_steps(d["id"])
        results.append(d)
    return results


def get_latest_plan(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent run containing a non-empty plan for project_id.
    """
    row = fetch_one(
        """
        SELECT * FROM runs
        WHERE project_id = ? AND plan_text IS NOT NULL AND TRIM(plan_text) != ''
        ORDER BY created_at DESC LIMIT 1
        """,
        (project_id,),
    )
    if row is None:
        return None
    return dict(row)


def update_plan_approval(project_id: str, plan_text: str) -> Optional[Dict[str, Any]]:
    """
    Update the latest plan for project_id or save an approved plan run.
    """
    latest = get_latest_plan(project_id)
    if latest:
        return update_run(
            latest["id"],
            plan_text=plan_text,
            status="approved",
        )

    # If no run with plan exists, create one
    return save_run(
        project_id=project_id,
        run_type="plan",
        prompt="User approved plan",
        plan_text=plan_text,
        status="approved",
    )
