"""
Traceability storage and link manager for Ojas.

Manages bidirectional links between:
- Requirements (REQ-xxx)
- Code chunks & symbols
- Test cases (TC-xxx)
- Bug reports (B-xxx)

Computes requirement coverage and traceability matrices.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.storage.db import get_db

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def link_req_to_code(
    project_id: str,
    req_id: str,
    code_chunk_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> str:
    """Link a requirement to a code chunk."""
    link_id = str(uuid.uuid4())
    ts = created_at or _now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO traceability_links (id, project_id, req_id, code_chunk_id, link_type, created_at)
            VALUES (?, ?, ?, ?, 'req_to_code', ?)
            """,
            (link_id, project_id, req_id, code_chunk_id, ts),
        )
        conn.commit()
    return link_id


def link_req_to_test(
    project_id: str,
    req_id: str,
    test_case_id: str,
    created_at: Optional[str] = None,
) -> str:
    """Link a requirement to a test case."""
    link_id = str(uuid.uuid4())
    ts = created_at or _now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO traceability_links (id, project_id, req_id, test_case_id, link_type, created_at)
            VALUES (?, ?, ?, ?, 'req_to_test', ?)
            """,
            (link_id, project_id, req_id, test_case_id, ts),
        )
        conn.commit()
    return link_id


def link_test_to_bug(
    project_id: str,
    test_case_id: str,
    bug_report_id: str,
    created_at: Optional[str] = None,
) -> str:
    """Link a test case to a bug report."""
    link_id = str(uuid.uuid4())
    ts = created_at or _now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO traceability_links (id, project_id, test_case_id, bug_report_id, link_type, created_at)
            VALUES (?, ?, ?, ?, 'test_to_bug', ?)
            """,
            (link_id, project_id, test_case_id, bug_report_id, ts),
        )
        conn.commit()
    return link_id


def link_code_to_bug(
    project_id: str,
    code_chunk_id: str,
    bug_report_id: str,
    created_at: Optional[str] = None,
) -> str:
    """Link a code chunk to a bug report."""
    link_id = str(uuid.uuid4())
    ts = created_at or _now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO traceability_links (id, project_id, code_chunk_id, bug_report_id, link_type, created_at)
            VALUES (?, ?, ?, ?, 'code_to_bug', ?)
            """,
            (link_id, project_id, code_chunk_id, bug_report_id, ts),
        )
        conn.commit()
    return link_id


def get_traceability_links(project_id: str, link_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve traceability links for a project with optional link_type filter."""
    with get_db() as conn:
        if link_type:
            cursor = conn.execute(
                """
                SELECT id, project_id, req_id, code_chunk_id, test_case_id, bug_report_id, link_type, created_at
                FROM traceability_links
                WHERE project_id = ? AND link_type = ?
                ORDER BY created_at ASC
                """,
                (project_id, link_type),
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, project_id, req_id, code_chunk_id, test_case_id, bug_report_id, link_type, created_at
                FROM traceability_links
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            )
        rows = cursor.fetchall()

    return [
        {
            "id": r[0],
            "project_id": r[1],
            "req_id": r[2],
            "code_chunk_id": r[3],
            "test_case_id": r[4],
            "bug_report_id": r[5],
            "link_type": r[6],
            "created_at": r[7],
        }
        for r in rows
    ]


def auto_sync_traceability(project_id: str) -> int:
    """
    Synchronise explicit links table from code_chunks, test_cases, and bug_reports.
    Returns the count of new links created.
    """
    new_links = 0
    with get_db() as conn:
        # 1. Inspect test_cases linked_req_ids
        tc_cursor = conn.execute(
            "SELECT id, tc_id, linked_req_ids FROM test_cases WHERE project_id = ?",
            (project_id,),
        )
        for tc_id_pk, tc_disp_id, raw_reqs in tc_cursor.fetchall():
            try:
                req_list = json.loads(raw_reqs) if raw_reqs else []
            except Exception:
                req_list = []
            for req in req_list:
                # Check if exists
                chk = conn.execute(
                    """
                    SELECT id FROM traceability_links
                    WHERE project_id = ? AND req_id = ? AND test_case_id = ? AND link_type = 'req_to_test'
                    """,
                    (project_id, req, tc_id_pk),
                ).fetchone()
                if not chk:
                    link_id = str(uuid.uuid4())
                    conn.execute(
                        """
                        INSERT INTO traceability_links (id, project_id, req_id, test_case_id, link_type, created_at)
                        VALUES (?, ?, ?, ?, 'req_to_test', ?)
                        """,
                        (link_id, project_id, req, tc_id_pk, _now_iso()),
                    )
                    new_links += 1

        # 2. Inspect bug_reports for req_id and tc_id
        bug_cursor = conn.execute(
            "SELECT id, bug_id, req_id, tc_id FROM bug_reports WHERE project_id = ?",
            (project_id,),
        )
        for bug_id_pk, bug_disp_id, req_id, tc_disp_id in bug_cursor.fetchall():
            if tc_disp_id:
                tc_row = conn.execute(
                    "SELECT id FROM test_cases WHERE project_id = ? AND tc_id = ?",
                    (project_id, tc_disp_id),
                ).fetchone()
                if tc_row:
                    tc_pk = tc_row[0]
                    chk = conn.execute(
                        """
                        SELECT id FROM traceability_links
                        WHERE project_id = ? AND test_case_id = ? AND bug_report_id = ? AND link_type = 'test_to_bug'
                        """,
                        (project_id, tc_pk, bug_id_pk),
                    ).fetchone()
                    if not chk:
                        conn.execute(
                            """
                            INSERT INTO traceability_links (id, project_id, test_case_id, bug_report_id, link_type, created_at)
                            VALUES (?, ?, ?, ?, 'test_to_bug', ?)
                            """,
                            (str(uuid.uuid4()), project_id, tc_pk, bug_id_pk, _now_iso()),
                        )
                        new_links += 1

        # 3. Inspect code_chunks for linked_req_ids
        chunk_cursor = conn.execute(
            "SELECT id, linked_req_ids FROM code_chunks WHERE project_id = ?",
            (project_id,),
        )
        for chunk_pk, raw_reqs in chunk_cursor.fetchall():
            try:
                req_list = json.loads(raw_reqs) if raw_reqs else []
            except Exception:
                req_list = []
            for req in req_list:
                chk = conn.execute(
                    """
                    SELECT id FROM traceability_links
                    WHERE project_id = ? AND req_id = ? AND code_chunk_id = ? AND link_type = 'req_to_code'
                    """,
                    (project_id, req, chunk_pk),
                ).fetchone()
                if not chk:
                    conn.execute(
                        """
                        INSERT INTO traceability_links (id, project_id, req_id, code_chunk_id, link_type, created_at)
                        VALUES (?, ?, ?, ?, 'req_to_code', ?)
                        """,
                        (str(uuid.uuid4()), project_id, req, chunk_pk, _now_iso()),
                    )
                    new_links += 1

        conn.commit()

    return new_links


def get_coverage(project_id: str) -> List[Dict[str, Any]]:
    """
    Return requirement coverage analysis for a project.

    For each requirement found in document chunks:
      - heading / title
      - linked code symbols / files
      - linked test cases
      - test results (pass / fail / not_run)
      - open bugs
      - coverage status: 'passing' | 'failing' | 'uncovered' | 'partial'
    """
    auto_sync_traceability(project_id)

    with get_db() as conn:
        # 1. Fetch requirements from document chunks or requirements tables
        req_rows = conn.execute(
            """
            SELECT DISTINCT req_id, heading, content
            FROM chunks
            WHERE project_id = ? AND req_id IS NOT NULL AND req_id != ''
            ORDER BY req_id ASC
            """,
            (project_id,),
        ).fetchall()

        # If no chunks with req_id found, also check traceability_links
        req_dict: Dict[str, Dict[str, Any]] = {}
        for r_id, heading, content_text in req_rows:
            req_dict[r_id] = {
                "req_id": r_id,
                "heading": heading or f"Requirement {r_id}",
                "description": (content_text[:120] + "...") if content_text and len(content_text) > 120 else (content_text or ""),
                "code_symbols": [],
                "test_cases": [],
                "results": [],
                "bugs": [],
                "status": "uncovered",
            }

        # Also populate any req_id that was linked via test cases or links
        extra_reqs = conn.execute(
            "SELECT DISTINCT req_id FROM traceability_links WHERE project_id = ? AND req_id IS NOT NULL",
            (project_id,),
        ).fetchall()
        for (er_id,) in extra_reqs:
            if er_id and er_id not in req_dict:
                req_dict[er_id] = {
                    "req_id": er_id,
                    "heading": f"Requirement {er_id}",
                    "description": "",
                    "code_symbols": [],
                    "test_cases": [],
                    "results": [],
                    "bugs": [],
                    "status": "uncovered",
                }

        # 2. Fetch code chunks linked
        code_links = conn.execute(
            """
            SELECT tl.req_id, cc.file_path, cc.symbol_name, cc.start_line, cc.end_line
            FROM traceability_links tl
            JOIN code_chunks cc ON tl.code_chunk_id = cc.id
            WHERE tl.project_id = ? AND tl.link_type = 'req_to_code'
            """,
            (project_id,),
        ).fetchall()
        for r_id, fpath, sym, start_l, end_l in code_links:
            if r_id in req_dict:
                req_dict[r_id]["code_symbols"].append(
                    {
                        "file_path": fpath,
                        "symbol_name": sym or fpath,
                        "start_line": start_l,
                        "end_line": end_l,
                    }
                )

        # 3. Fetch test cases linked & their latest test result
        tc_links = conn.execute(
            """
            SELECT tl.req_id, tc.id, tc.tc_id, tc.name, tc.status
            FROM traceability_links tl
            JOIN test_cases tc ON tl.test_case_id = tc.id
            WHERE tl.project_id = ? AND tl.link_type = 'req_to_test'
            """,
            (project_id,),
        ).fetchall()

        for r_id, tc_pk, tc_disp, tc_name, tc_status in tc_links:
            if r_id in req_dict:
                req_dict[r_id]["test_cases"].append(
                    {
                        "id": tc_pk,
                        "tc_id": tc_disp,
                        "name": tc_name,
                        "status": tc_status or "not_run",
                    }
                )
                req_dict[r_id]["results"].append(
                    {
                        "tc_id": tc_disp,
                        "result": tc_status or "not_run",
                    }
                )

        # 4. Fetch bugs linked to requirements
        bug_rows = conn.execute(
            """
            SELECT bug_id, req_id, tc_id, severity, status, actual_result
            FROM bug_reports
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchall()
        for b_id, b_req, b_tc, sev, b_stat, act_res in bug_rows:
            if b_req and b_req in req_dict:
                req_dict[b_req]["bugs"].append(
                    {
                        "bug_id": b_id,
                        "tc_id": b_tc,
                        "title": act_res,
                        "severity": sev,
                        "status": b_stat,
                    }
                )
            elif b_tc:
                # Find matching req via test case
                for r_item in req_dict.values():
                    if any(t["tc_id"] == b_tc for t in r_item["test_cases"]):
                        if not any(b["bug_id"] == b_id for b in r_item["bugs"]):
                            r_item["bugs"].append(
                                {
                                    "bug_id": b_id,
                                    "tc_id": b_tc,
                                    "title": act_res,
                                    "severity": sev,
                                    "status": b_stat,
                                }
                            )

        # 5. Determine status
        for r_item in req_dict.values():
            tests = r_item["test_cases"]
            results = [t["status"] for t in tests]
            if not tests:
                r_item["status"] = "uncovered"
            elif any(r in ("failed", "error") for r in results):
                r_item["status"] = "failing"
            elif all(r == "passed" for r in results):
                r_item["status"] = "passing"
            else:
                r_item["status"] = "partial"

    return list(req_dict.values())
