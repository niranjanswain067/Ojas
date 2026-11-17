"""
Storage and repository layer for Projects.
Interacts directly with SQLite database and workspace filesystem directories.
"""

import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.storage.db import execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)

# Project root: backend/app/storage/project_store.py -> 4 levels up
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def get_workspace_dir(project_id: str) -> Path:
    """Return the absolute path to a project's workspace folder."""
    return _PROJECT_ROOT / "workspace" / project_id


def get_reports_dir(project_id: str) -> Path:
    """Return the absolute path to a project's reports folder."""
    return _PROJECT_ROOT / "reports" / project_id


def create_project(name: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new project in the database and initialize its workspace folder.

    Raises:
        ValueError: If a project with the same name already exists.
    """
    trimmed_name = name.strip()
    if not trimmed_name:
        raise ValueError("Project name cannot be empty.")

    # Check for duplicate project name
    existing = fetch_one("SELECT id FROM projects WHERE name = ?", (trimmed_name,))
    if existing:
        raise ValueError(f"Project with name '{trimmed_name}' already exists.")

    project_id = str(uuid.uuid4())
    now = _now_iso()

    # 1. Initialize workspace directory on disk
    ws_path = get_workspace_dir(project_id)
    ws_path.mkdir(parents=True, exist_ok=True)
    # Also create subdirectories for documents and tests if helpful
    (ws_path / "documents").mkdir(exist_ok=True)
    (ws_path / "tests").mkdir(exist_ok=True)

    # 2. Insert record into database
    execute_query(
        """
        INSERT INTO projects (id, name, description, status, created_at, updated_at)
        VALUES (?, ?, ?, 'idle', ?, ?)
        """,
        (project_id, trimmed_name, description.strip(), now, now),
    )

    logger.info("Created project %s ('%s') at %s", project_id, trimmed_name, ws_path)

    return {
        "id": project_id,
        "name": trimmed_name,
        "description": description.strip(),
        "status": "idle",
        "document_count": 0,
        "requirement_count": 0,
        "test_case_count": 0,
        "test_count": 0,
        "bug_count": 0,
        "run_count": 0,
        "last_run_result": None,
        "created_at": now,
        "updated_at": now,
    }


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve project details along with aggregate counts for documents,
    requirements, tests, bugs, and runs.
    """
    row = fetch_one(
        """
        SELECT id, name, description, status, created_at, updated_at
        FROM projects
        WHERE id = ?
        """,
        (project_id,),
    )
    if not row:
        return None

    # Compute aggregate counts
    doc_row = fetch_one("SELECT COUNT(*) AS c FROM documents WHERE project_id = ?", (project_id,))
    doc_count = doc_row["c"] if doc_row else 0

    req_row = fetch_one(
        "SELECT COUNT(*) AS c FROM chunks WHERE project_id = ? AND req_id IS NOT NULL",
        (project_id,),
    )
    req_count = req_row["c"] if req_row else 0

    test_row = fetch_one("SELECT COUNT(*) AS c FROM test_cases WHERE project_id = ?", (project_id,))
    test_count = test_row["c"] if test_row else 0

    bug_row = fetch_one("SELECT COUNT(*) AS c FROM bug_reports WHERE project_id = ?", (project_id,))
    bug_count = bug_row["c"] if bug_row else 0

    run_row = fetch_one("SELECT COUNT(*) AS c FROM runs WHERE project_id = ?", (project_id,))
    run_count = run_row["c"] if run_row else 0

    last_run = fetch_one(
        "SELECT stop_reason, status FROM runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    )
    last_run_result = None
    if last_run:
        last_run_result = last_run.get("stop_reason") or last_run.get("status")

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "status": row["status"] or "idle",
        "document_count": doc_count,
        "requirement_count": req_count,
        "test_case_count": test_count,
        "test_count": test_count,
        "bug_count": bug_count,
        "run_count": run_count,
        "last_run_result": last_run_result,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_projects() -> List[Dict[str, Any]]:
    """
    List all projects ordered by updated_at descending, including aggregate counts.
    """
    projects = fetch_all(
        """
        SELECT 
            p.id,
            p.name,
            p.description,
            p.status,
            p.created_at,
            p.updated_at,
            COUNT(DISTINCT d.id) AS document_count,
            COUNT(DISTINCT c.id) AS requirement_count,
            COUNT(DISTINCT t.id) AS test_case_count,
            COUNT(DISTINCT b.id) AS bug_count,
            COUNT(DISTINCT r.id) AS run_count
        FROM projects p
        LEFT JOIN documents d ON d.project_id = p.id
        LEFT JOIN chunks c ON c.project_id = p.id AND c.req_id IS NOT NULL
        LEFT JOIN test_cases t ON t.project_id = p.id
        LEFT JOIN bug_reports b ON b.project_id = p.id
        LEFT JOIN runs r ON r.project_id = p.id
        GROUP BY p.id
        ORDER BY p.updated_at DESC
        """
    )

    results = []
    for p in projects:
        # Get latest run result for project
        last_run = fetch_one(
            "SELECT stop_reason, status FROM runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
            (p["id"],),
        )
        last_run_result = None
        if last_run:
            last_run_result = last_run.get("stop_reason") or last_run.get("status")

        test_count = p["test_case_count"]
        results.append({
            "id": p["id"],
            "name": p["name"],
            "description": p["description"] or "",
            "status": p["status"] or "idle",
            "document_count": p["document_count"],
            "requirement_count": p["requirement_count"],
            "test_case_count": test_count,
            "test_count": test_count,
            "bug_count": p["bug_count"],
            "run_count": p["run_count"],
            "last_run_result": last_run_result,
            "created_at": p["created_at"],
            "updated_at": p["updated_at"],
        })

    return results


def update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update project name and/or description.

    Raises:
        ValueError: If the new name conflicts with an existing project.
    """
    existing = get_project(project_id)
    if not existing:
        return None

    new_name = name.strip() if name is not None else existing["name"]
    if not new_name:
        raise ValueError("Project name cannot be empty.")

    # Check if name is taken by another project
    if new_name != existing["name"]:
        duplicate = fetch_one(
            "SELECT id FROM projects WHERE name = ? AND id != ?",
            (new_name, project_id),
        )
        if duplicate:
            raise ValueError(f"Another project with name '{new_name}' already exists.")

    new_desc = description.strip() if description is not None else existing["description"]
    now = _now_iso()

    execute_query(
        """
        UPDATE projects
        SET name = ?, description = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_name, new_desc, now, project_id),
    )

    logger.info("Updated project %s ('%s')", project_id, new_name)
    return get_project(project_id)


def delete_project(project_id: str) -> bool:
    """
    Delete a project from SQLite (CASCADE handles related records)
    and removes its workspace and reports directories.

    Raises:
        RuntimeError: If a run is currently active for this project.
    """
    existing = get_project(project_id)
    if not existing:
        return False

    # Prevent deleting if a run is actively running
    active_run = fetch_one(
        "SELECT id FROM runs WHERE project_id = ? AND status = 'running' LIMIT 1",
        (project_id,),
    )
    if active_run:
        raise RuntimeError("Cannot delete project while an active run is in progress.")

    # 1. Delete from database (foreign keys ON DELETE CASCADE clean up children)
    execute_query("DELETE FROM projects WHERE id = ?", (project_id,))

    # 2. Clean up workspace directory
    ws_dir = get_workspace_dir(project_id)
    if ws_dir.exists():
        try:
            shutil.rmtree(ws_dir)
            logger.info("Deleted workspace directory: %s", ws_dir)
        except Exception as e:
            logger.warning("Failed to fully delete workspace directory %s: %s", ws_dir, e)

    # 3. Clean up reports directory if present
    rep_dir = get_reports_dir(project_id)
    if rep_dir.exists():
        try:
            shutil.rmtree(rep_dir)
            logger.info("Deleted reports directory: %s", rep_dir)
        except Exception as e:
            logger.warning("Failed to fully delete reports directory %s: %s", rep_dir, e)

    return True
