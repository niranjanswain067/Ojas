"""
Database store for bug reports created during test failure analysis.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.storage.db import execute_query, fetch_all, fetch_one
from backend.app.storage.document_store import ensure_project

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def get_next_bug_id(project_id: str) -> str:
    """Generate sequential Bug ID (e.g. B-001, B-002) for a project."""
    rows = fetch_all(
        "SELECT bug_id FROM bug_reports WHERE project_id = ? ORDER BY bug_id ASC",
        (project_id,),
    )
    max_num = 0
    for r in rows:
        bid = r["bug_id"] if isinstance(r, dict) else r[0]
        match = re.search(r"B-(\d+)", bid, re.IGNORECASE)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"B-{max_num + 1:03d}"


def save_bug_report(
    project_id: str,
    run_id: str,
    bug_id: str,
    expected_result: str,
    actual_result: str,
    req_id: Optional[str] = None,
    tc_id: Optional[str] = None,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    severity: str = "medium",
    probable_cause: Optional[str] = None,
    iteration: int = 0,
    status: str = "open",
    fix_description: Optional[str] = None,
    report_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert or update a bug report in bug_reports table."""
    ensure_project(project_id)
    from backend.app.storage.run_store import get_run, save_run

    if not get_run(run_id):
        save_run(project_id=project_id, run_type="test", run_id=run_id)

    b_id = report_id or str(uuid.uuid4())
    now = _now_iso()

    existing = fetch_one(
        "SELECT id FROM bug_reports WHERE project_id = ? AND bug_id = ?",
        (project_id, bug_id),
    )
    if existing:
        b_id = existing["id"]
        execute_query(
            """
            UPDATE bug_reports SET
                run_id = ?, req_id = ?, tc_id = ?, file_path = ?, function_name = ?,
                severity = ?, expected_result = ?, actual_result = ?, probable_cause = ?,
                iteration = ?, status = ?, fix_description = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                run_id,
                req_id,
                tc_id,
                file_path,
                function_name,
                severity,
                expected_result,
                actual_result,
                probable_cause,
                iteration,
                status,
                fix_description,
                now,
                b_id,
            ),
        )
    else:
        execute_query(
            """
            INSERT INTO bug_reports (
                id, project_id, run_id, bug_id, req_id, tc_id, file_path, function_name,
                severity, expected_result, actual_result, probable_cause, iteration,
                status, fix_description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                b_id,
                project_id,
                run_id,
                bug_id,
                req_id,
                tc_id,
                file_path,
                function_name,
                severity,
                expected_result,
                actual_result,
                probable_cause,
                iteration,
                status,
                fix_description,
                now,
                now,
            ),
        )

    return get_bug_report(b_id) or {}


def get_bug_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve bug report by primary key or bug_id."""
    row = fetch_one("SELECT * FROM bug_reports WHERE id = ? OR bug_id = ?", (report_id, report_id))
    return dict(row) if row else None


def get_bug_reports(
    project_id: str,
    run_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve bug reports for a project, optionally filtered by run_id or status."""
    sql = "SELECT * FROM bug_reports WHERE project_id = ?"
    params: List[Any] = [project_id]

    if run_id:
        sql += " AND run_id = ?"
        params.append(run_id)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY created_at DESC"
    rows = fetch_all(sql, tuple(params))
    return [dict(r) for r in rows]


def update_bug_report_status(
    report_id: str,
    status: str,
    fix_description: Optional[str] = None,
) -> None:
    """Update status and optional fix description for a bug report."""
    now = _now_iso()
    if fix_description is not None:
        execute_query(
            "UPDATE bug_reports SET status = ?, fix_description = ?, updated_at = ? WHERE id = ? OR bug_id = ?",
            (status, fix_description, now, report_id, report_id),
        )
    else:
        execute_query(
            "UPDATE bug_reports SET status = ?, updated_at = ? WHERE id = ? OR bug_id = ?",
            (status, now, report_id, report_id),
        )
