"""
Database store for test cases and test execution results.
Handles AST parsing of test files to discover test functions and extract REQ-IDs.
"""

import ast
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.storage.db import execute_query, fetch_all, fetch_one
from backend.app.storage.document_store import ensure_project

logger = logging.getLogger(__name__)

_REQ_PATTERN = re.compile(r"REQ-\d+", re.IGNORECASE)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def get_next_tc_id(project_id: str) -> str:
    """Generate the next sequential TC ID (e.g. TC-001, TC-002) for a project."""
    rows = fetch_all(
        "SELECT tc_id FROM test_cases WHERE project_id = ? ORDER BY tc_id ASC",
        (project_id,),
    )
    max_num = 0
    for r in rows:
        tc = r["tc_id"] if isinstance(r, dict) else r[0]
        match = re.search(r"TC-(\d+)", tc, re.IGNORECASE)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"TC-{max_num + 1:03d}"


def extract_test_cases_from_code(code: str, file_path: str) -> List[Dict[str, Any]]:
    """
    Parse Python source code with AST to discover test functions and classes.
    Extracts function name, docstring, and linked requirement IDs.
    """
    discovered: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(code, filename=file_path)
    except Exception as exc:
        logger.warning("AST parse failed for %s: %s", file_path, exc)
        return discovered

    # Scan top-level and class-level functions
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            docstring = ast.get_docstring(node) or ""
            req_matches = _REQ_PATTERN.findall(f"{node.name} {docstring}")
            req_ids = sorted(list({m.upper() for m in req_matches}))
            discovered.append({
                "name": docstring.strip() if docstring else node.name,
                "function_name": node.name,
                "file_path": file_path,
                "linked_req_ids": req_ids,
            })
        elif isinstance(node, ast.ClassDef) and (node.name.startswith("Test") or node.name.endswith("Test")):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    docstring = ast.get_docstring(item) or ""
                    combo = f"{node.name}.{item.name}"
                    req_matches = _REQ_PATTERN.findall(f"{combo} {docstring}")
                    req_ids = sorted(list({m.upper() for m in req_matches}))
                    discovered.append({
                        "name": docstring.strip() if docstring else combo,
                        "function_name": combo,
                        "file_path": file_path,
                        "linked_req_ids": req_ids,
                    })

    return discovered


def save_test_case(
    project_id: str,
    tc_id: str,
    name: str,
    file_path: str,
    function_name: Optional[str] = None,
    linked_req_ids: Optional[List[str]] = None,
    source: str = "user",
    status: str = "not_run",
    test_case_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert or update a test case in test_cases table."""
    ensure_project(project_id)
    t_id = test_case_id or str(uuid.uuid4())
    now = _now_iso()
    reqs_json = json.dumps(linked_req_ids or [])

    # Check if tc_id exists for project
    existing = fetch_one(
        "SELECT id FROM test_cases WHERE project_id = ? AND tc_id = ?",
        (project_id, tc_id),
    )
    if existing:
        t_id = existing["id"]
        execute_query(
            """
            UPDATE test_cases SET
                name = ?, file_path = ?, function_name = ?, linked_req_ids = ?,
                source = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, file_path, function_name, reqs_json, source, status, now, t_id),
        )
    else:
        execute_query(
            """
            INSERT INTO test_cases (
                id, project_id, tc_id, name, file_path, function_name,
                linked_req_ids, source, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (t_id, project_id, tc_id, name, file_path, function_name, reqs_json, source, status, now, now),
        )

    return get_test_case(t_id) or {}


def register_test_file(
    project_id: str,
    file_path: str,
    code: str,
    source: str = "user",
) -> List[Dict[str, Any]]:
    """
    Extract all test functions from code and save/update them in test_cases table.
    """
    ensure_project(project_id)
    items = extract_test_cases_from_code(code, file_path)
    registered = []

    for item in items:
        # Check if function already registered in this file
        existing = fetch_one(
            "SELECT * FROM test_cases WHERE project_id = ? AND file_path = ? AND function_name = ?",
            (project_id, file_path, item["function_name"]),
        )
        if existing:
            tc_id = existing["tc_id"]
            tc_record_id = existing["id"]
        else:
            tc_id = get_next_tc_id(project_id)
            tc_record_id = None

        record = save_test_case(
            project_id=project_id,
            tc_id=tc_id,
            name=item["name"],
            file_path=file_path,
            function_name=item["function_name"],
            linked_req_ids=item["linked_req_ids"],
            source=source,
            status="not_run",
            test_case_id=tc_record_id,
        )
        registered.append(record)

    return registered


def get_test_case(test_case_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve test case by primary key ID."""
    row = fetch_one("SELECT * FROM test_cases WHERE id = ?", (test_case_id,))
    if not row:
        return None
    data = dict(row)
    if isinstance(data.get("linked_req_ids"), str):
        try:
            data["linked_req_ids"] = json.loads(data["linked_req_ids"])
        except Exception:
            data["linked_req_ids"] = []
    return data


def get_test_case_by_tc_id(project_id: str, tc_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve test case by project_id and tc_id."""
    row = fetch_one(
        "SELECT * FROM test_cases WHERE project_id = ? AND tc_id = ?",
        (project_id, tc_id),
    )
    if not row:
        return None
    data = dict(row)
    if isinstance(data.get("linked_req_ids"), str):
        try:
            data["linked_req_ids"] = json.loads(data["linked_req_ids"])
        except Exception:
            data["linked_req_ids"] = []
    return data


def get_test_case_by_name_or_function(project_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Retrieve test case matching function name or name."""
    row = fetch_one(
        "SELECT * FROM test_cases WHERE project_id = ? AND (function_name = ? OR name = ?)",
        (project_id, name, name),
    )
    if not row:
        return None
    data = dict(row)
    if isinstance(data.get("linked_req_ids"), str):
        try:
            data["linked_req_ids"] = json.loads(data["linked_req_ids"])
        except Exception:
            data["linked_req_ids"] = []
    return data


def get_test_cases(project_id: str) -> List[Dict[str, Any]]:
    """Retrieve all test cases for a project ordered by tc_id."""
    rows = fetch_all(
        "SELECT * FROM test_cases WHERE project_id = ? ORDER BY tc_id ASC",
        (project_id,),
    )
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("linked_req_ids"), str):
            try:
                d["linked_req_ids"] = json.loads(d["linked_req_ids"])
            except Exception:
                d["linked_req_ids"] = []
        results.append(d)
    return results


def update_test_case_status(test_case_id: str, status: str) -> None:
    """Update status column for a test case."""
    now = _now_iso()
    execute_query(
        "UPDATE test_cases SET status = ?, updated_at = ? WHERE id = ?",
        (status, now, test_case_id),
    )


# ---------------------------------------------------------------------------
# Test Results
# ---------------------------------------------------------------------------


def save_test_result(
    run_id: str,
    test_case_id: str,
    tc_id: str,
    result: str,
    iteration: int = 0,
    duration_ms: Optional[int] = None,
    stdout: str = "",
    stderr: str = "",
    error_message: Optional[str] = None,
    result_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Save an individual test execution result."""
    r_id = result_id or str(uuid.uuid4())
    now = _now_iso()

    # Ensure test case exists in test_cases table
    tc_row = fetch_one("SELECT project_id FROM test_cases WHERE id = ?", (test_case_id,))
    if not tc_row:
        p_id = project_id or "default-project"
        save_test_case(
            project_id=p_id,
            tc_id=tc_id or "TC-001",
            name=tc_id or "Test",
            file_path="tests/test_suite.py",
            test_case_id=test_case_id,
        )
        proj_id = p_id
    else:
        proj_id = tc_row["project_id"]

    # Ensure run exists in runs table
    from backend.app.storage.run_store import get_run, save_run

    if not get_run(run_id):
        save_run(project_id=proj_id, run_type="test", run_id=run_id)

    execute_query(
        """
        INSERT INTO test_results (
            id, run_id, test_case_id, tc_id, iteration, result,
            duration_ms, stdout, stderr, error_message, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (r_id, run_id, test_case_id, tc_id, iteration, result, duration_ms, stdout, stderr, error_message, now),
    )

    # Also update current status on test_cases
    update_test_case_status(test_case_id, result)

    return {
        "id": r_id,
        "run_id": run_id,
        "test_case_id": test_case_id,
        "tc_id": tc_id,
        "iteration": iteration,
        "result": result,
        "duration_ms": duration_ms,
        "stdout": stdout,
        "stderr": stderr,
        "error_message": error_message,
        "created_at": now,
    }


def get_test_results(run_id: str) -> List[Dict[str, Any]]:
    """Retrieve all test execution results for a specific run."""
    rows = fetch_all(
        "SELECT * FROM test_results WHERE run_id = ? ORDER BY tc_id ASC, iteration ASC, created_at ASC",
        (run_id,),
    )
    return [dict(r) for r in rows]


def get_latest_test_results(project_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve latest test results for a project by joining with runs table.
    """
    rows = fetch_all(
        """
        SELECT tr.* FROM test_results tr
        JOIN runs r ON tr.run_id = r.id
        WHERE r.project_id = ?
        ORDER BY tr.created_at DESC LIMIT 100
        """,
        (project_id,),
    )
    return [dict(r) for r in rows]
