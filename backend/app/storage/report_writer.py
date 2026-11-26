"""
Report generator for Ojas.

Generates structured Markdown and JSON reports for:
- Development Plan
- Bug Reports
- Test Results
- Consolidated Quality & Traceability Report

Saves reports to reports/<project_id>/ directory.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.storage.db import get_db
from backend.app.storage.traceability import get_coverage

logger = logging.getLogger(__name__)

# Project root: 3 levels up from this file (backend/app/storage/report_writer.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReportWriter:
    """Manages report compilation, formatting, and file persistence."""

    def __init__(self, project_id: str, base_reports_dir: Optional[Path] = None) -> None:
        self.project_id = project_id
        root = base_reports_dir or (_PROJECT_ROOT / "reports")
        self.reports_dir = root / project_id
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_name(self) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT name FROM projects WHERE id = ?",
                (self.project_id,),
            ).fetchone()
            if row and row[0]:
                return row[0]
        return self.project_id

    # ------------------------------------------------------------------
    # Individual Reports
    # ------------------------------------------------------------------

    def generate_development_plan_report(
        self,
        plan_text: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> str:
        """Generate and save the Development Plan report."""
        proj_name = self._get_project_name()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if not plan_text:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT plan_text, id FROM runs WHERE project_id = ? AND plan_text IS NOT NULL ORDER BY created_at DESC LIMIT 1",
                    (self.project_id,),
                ).fetchone()
                if row:
                    plan_text = row[0]
                    run_id = run_id or row[1]

        content = f"""# Development Plan Report
**Project:** {proj_name} (`{self.project_id}`)  
**Generated At:** {ts}  
**Run ID:** `{run_id or 'N/A'}`  

---

## Plan Specification

{plan_text or '_No development plan recorded yet._'}
"""
        out_path = self.reports_dir / "development_plan.md"
        out_path.write_text(content, encoding="utf-8")
        return content

    def generate_bug_report(
        self,
        bugs: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate and save the Bug Report."""
        proj_name = self._get_project_name()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if bugs is None:
            with get_db() as conn:
                cursor = conn.execute(
                    """
                    SELECT bug_id, actual_result, severity, status, req_id, tc_id, file_path, function_name, expected_result, fix_description
                    FROM bug_reports
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    """,
                    (self.project_id,),
                )
                bugs = [
                    {
                        "bug_id": r[0],
                        "title": r[1],
                        "severity": r[2],
                        "status": r[3],
                        "req_id": r[4],
                        "tc_id": r[5],
                        "file_path": r[6],
                        "function_name": r[7],
                        "expected": r[8],
                        "actual": r[1],
                        "fix_status": r[9],
                    }
                    for r in cursor.fetchall()
                ]

        open_count = sum(1 for b in bugs if b.get("status") == "open")
        resolved_count = sum(1 for b in bugs if b.get("status") in ("resolved", "fixed"))

        table_rows = []
        for b in bugs:
            b_id = b.get("bug_id", "-")
            sev = b.get("severity", "medium").upper()
            status = b.get("status", "open")
            tc = b.get("tc_id") or "-"
            req = b.get("req_id") or "-"
            loc = f"`{b.get('file_path') or '-'}:{b.get('function_name') or '-'}`"
            title = b.get("title") or b.get("actual") or "Bug"
            table_rows.append(f"| `{b_id}` | {title} | **{sev}** | {status} | `{req}` | `{tc}` | {loc} |")

        table_md = "\n".join(table_rows) if table_rows else "| - | No bugs recorded | - | - | - | - | - |"

        content = f"""# Bug Reports Summary
**Project:** {proj_name} (`{self.project_id}`)  
**Generated At:** {ts}  
**Total Bugs:** {len(bugs)} (Open: {open_count}, Resolved: {resolved_count})  

---

| Bug ID | Title / Issue | Severity | Status | REQ-ID | TC-ID | Location |
|---|---|---|---|---|---|---|
{table_md}
"""
        out_path = self.reports_dir / "bug_report.md"
        out_path.write_text(content, encoding="utf-8")
        return content

    def generate_test_report(
        self,
        results: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate and save the Test Results report."""
        proj_name = self._get_project_name()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if results is None:
            with get_db() as conn:
                cursor = conn.execute(
                    """
                    SELECT tc.tc_id, tc.name, tc.file_path, tc.function_name, tc.status, tr.iteration, tr.duration_ms, tr.error_message
                    FROM test_cases tc
                    LEFT JOIN test_results tr ON tc.id = tr.test_case_id
                    WHERE tc.project_id = ?
                    ORDER BY tc.tc_id ASC, tr.iteration DESC
                    """,
                    (self.project_id,),
                )
                seen_tc = set()
                results = []
                for r in cursor.fetchall():
                    tc_id = r[0]
                    if tc_id in seen_tc:
                        continue
                    seen_tc.add(tc_id)
                    results.append(
                        {
                            "tc_id": tc_id,
                            "name": r[1],
                            "file_path": r[2],
                            "function": r[3],
                            "status": r[4] or "not_run",
                            "iteration": r[5] or 0,
                            "duration_ms": r[6] or 0,
                            "error": r[7] or "",
                        }
                    )

        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") in ("failed", "error"))
        total = len(results)
        rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"

        table_rows = []
        for r in results:
            tc_id = r.get("tc_id", "-")
            name = r.get("name", "-")
            stat = r.get("status", "not_run")
            icon = "✅ PASSED" if stat == "passed" else ("❌ FAILED" if stat in ("failed", "error") else "⚪ NOT RUN")
            dur = f"{r.get('duration_ms', 0)} ms"
            table_rows.append(f"| `{tc_id}` | {name} | {icon} | {dur} |")

        table_md = "\n".join(table_rows) if table_rows else "| - | No test cases found | - | - |"

        content = f"""# Test Execution Report
**Project:** {proj_name} (`{self.project_id}`)  
**Generated At:** {ts}  
**Total Tests:** {total} | **Passed:** {passed} | **Failed:** {failed} | **Pass Rate:** {rate}  

---

| TC-ID | Test Case Name | Result | Duration |
|---|---|---|---|
{table_md}
"""
        out_path = self.reports_dir / "test_report.md"
        out_path.write_text(content, encoding="utf-8")
        return content

    # ------------------------------------------------------------------
    # Consolidated Quality & Traceability Report
    # ------------------------------------------------------------------

    def generate_consolidated_report(self) -> str:
        """
        Generate the complete Consolidated Quality, Traceability, and Execution Report.
        Saves to reports/<project_id>/consolidated_test_report.md.
        """
        proj_name = self._get_project_name()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Gather Summary Metrics
        with get_db() as conn:
            # Tests summary
            tc_stats = conn.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status IN ('failed', 'error') THEN 1 ELSE 0 END)
                FROM test_cases
                WHERE project_id = ?
                """,
                (self.project_id,),
            ).fetchone()
            total_tests = tc_stats[0] or 0
            passed_tests = tc_stats[1] or 0
            failed_tests = tc_stats[2] or 0

            # Runs & Iteration summary
            run_stats = conn.execute(
                """
                SELECT COUNT(*), COALESCE(MAX(iteration_count), 0)
                FROM runs
                WHERE project_id = ?
                """,
                (self.project_id,),
            ).fetchone()
            total_runs = run_stats[0] or 0
            max_iteration = run_stats[1] or 0
            total_time_s = 0

            # Compute approximate duration from runs
            dur_rows = conn.execute(
                "SELECT started_at, completed_at FROM runs WHERE project_id = ? AND started_at IS NOT NULL AND completed_at IS NOT NULL",
                (self.project_id,),
            ).fetchall()
            for s_at, c_at in dur_rows:
                try:
                    t1 = datetime.fromisoformat(s_at)
                    t2 = datetime.fromisoformat(c_at)
                    diff = int((t2 - t1).total_seconds())
                    if diff > 0:
                        total_time_s += diff
                except Exception:
                    pass

            # Bugs summary
            bug_stats = conn.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status IN ('resolved', 'fixed') THEN 1 ELSE 0 END)
                FROM bug_reports
                WHERE project_id = ?
                """,
                (self.project_id,),
            ).fetchone()
            total_bugs = bug_stats[0] or 0
            open_bugs = bug_stats[1] or 0
            fixed_bugs = bug_stats[2] or 0

            # Recent Runs
            recent_runs_cursor = conn.execute(
                """
                SELECT id, run_type, status, stop_reason, iteration_count, created_at, started_at, completed_at
                FROM runs
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (self.project_id,),
            )
            recent_runs = recent_runs_cursor.fetchall()

        pass_rate = f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0.0%"

        # 2. Coverage & Traceability Matrix
        coverage_items = get_coverage(self.project_id)
        coverage_rows = []
        for cov in coverage_items:
            req_id = cov.get("req_id", "-")
            heading = cov.get("heading", "-")
            symbols = ", ".join([f"`{s['symbol_name']}`" for s in cov.get("code_symbols", [])]) or "_None_"
            tests_list = [f"`{t['tc_id']}` ({t['status']})" for t in cov.get("test_cases", [])]
            tests_str = ", ".join(tests_list) if tests_list else "_None_"
            bugs_list = [f"`{b['bug_id']}` ({b['severity']})" for b in cov.get("bugs", [])]
            bugs_str = ", ".join(bugs_list) if bugs_list else "None"
            status = cov.get("status", "uncovered").upper()
            status_icon = "🟢 PASSING" if status == "PASSING" else ("🔴 FAILING" if status == "FAILING" else ("🟡 PARTIAL" if status == "PARTIAL" else "⚪ UNCOVERED"))
            coverage_rows.append(f"| `{req_id}` | {heading} | {symbols} | {tests_str} | {bugs_str} | {status_icon} |")

        coverage_md = "\n".join(coverage_rows) if coverage_rows else "| - | No requirements tracked | - | - | - | - |"

        # 3. Runs History Table
        runs_rows = []
        for r in recent_runs:
            r_id = r[0][:8]
            r_type = r[1]
            r_stat = r[2]
            r_stop = r[3] or "-"
            r_iter = r[4] or 0
            r_date = r[5][:19].replace("T", " ")
            dur_sec = 0
            if r[6] and r[7]:
                try:
                    dur_sec = max(0, int((datetime.fromisoformat(r[7]) - datetime.fromisoformat(r[6])).total_seconds()))
                except Exception:
                    pass
            runs_rows.append(f"| `{r_id}` | {r_type} | {r_stat} | {r_stop} | {r_iter} | {dur_sec}s | {r_date} |")

        runs_md = "\n".join(runs_rows) if runs_rows else "| - | No runs recorded | - | - | - | - | - |"

        content = f"""# Consolidated Quality & Traceability Report
**Project:** {proj_name} (`{self.project_id}`)  
**Generated At:** {ts}  

---

## 1. Executive Summary

| Metric | Value |
|---|---|
| **Total Test Cases** | {total_tests} |
| **Passing Tests** | {passed_tests} |
| **Failing Tests** | {failed_tests} |
| **Test Pass Rate** | **{pass_rate}** |
| **Total Fix Iterations** | {max_iteration} |
| **Total Execution Time** | {total_time_s} seconds |
| **Total Bugs Recorded** | {total_bugs} (Open: {open_bugs}, Fixed: {fixed_bugs}) |

---

## 2. Requirement Traceability Matrix

| REQ-ID | Heading | Code Symbols | Test Cases (Result) | Bugs | Status |
|---|---|---|---|---|---|
{coverage_md}

---

## 3. Recent Execution Runs

| Run ID | Type | Status | Stop Reason | Iteration | Duration | Started |
|---|---|---|---|---|---|---|
{runs_md}

---

*Report automatically generated by Ojas Local Platform.*
"""
        out_path = self.reports_dir / "consolidated_test_report.md"
        out_path.write_text(content, encoding="utf-8")

        # Also write consolidated_report.md alias
        (self.reports_dir / "consolidated_report.md").write_text(content, encoding="utf-8")

        return content

    def get_report_data(self, report_name: str) -> Dict[str, Any]:
        """Return structured data and content for a report."""
        clean_name = report_name.replace(".md", "")
        target_file = self.reports_dir / f"{clean_name}.md"

        if not target_file.is_file():
            # If not yet generated, generate it now
            if "plan" in clean_name:
                self.generate_development_plan_report()
            elif "bug" in clean_name:
                self.generate_bug_report()
            elif "test" in clean_name and "consolidated" not in clean_name:
                self.generate_test_report()
            else:
                self.generate_consolidated_report()

        content = target_file.read_text(encoding="utf-8") if target_file.is_file() else ""

        # Compute summary
        with get_db() as conn:
            tc_stats = conn.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status IN ('failed', 'error') THEN 1 ELSE 0 END)
                FROM test_cases
                WHERE project_id = ?
                """,
                (self.project_id,),
            ).fetchone()
            total_tests = tc_stats[0] or 0
            passed_tests = tc_stats[1] or 0
            failed_tests = tc_stats[2] or 0

            run_stats = conn.execute(
                "SELECT COALESCE(MAX(iteration_count), 0) FROM runs WHERE project_id = ?",
                (self.project_id,),
            ).fetchone()
            max_iteration = run_stats[0] or 0
            total_time_s = 0
            dur_rows = conn.execute(
                "SELECT started_at, completed_at FROM runs WHERE project_id = ? AND started_at IS NOT NULL AND completed_at IS NOT NULL",
                (self.project_id,),
            ).fetchall()
            for s_at, c_at in dur_rows:
                try:
                    diff = int((datetime.fromisoformat(c_at) - datetime.fromisoformat(s_at)).total_seconds())
                    if diff > 0:
                        total_time_s += diff
                except Exception:
                    pass

        coverage_items = get_coverage(self.project_id)
        coverage_data = [
            {
                "req_id": c["req_id"],
                "heading": c["heading"],
                "tests": [{"tc_id": t["tc_id"], "result": t["status"]} for t in c.get("test_cases", [])],
                "bugs": [b["bug_id"] for b in c.get("bugs", [])],
                "status": c.get("status", "uncovered"),
            }
            for c in coverage_items
        ]

        title_map = {
            "development_plan": "Development Plan",
            "consolidated_test_report": "Consolidated Test Report",
            "consolidated_report": "Consolidated Quality Report",
            "test_report": "Test Execution Report",
            "bug_report": "Bug Reports Summary",
        }

        return {
            "report_name": clean_name,
            "title": title_map.get(clean_name, clean_name.replace("_", " ").title()),
            "content": content,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "iterations": max_iteration,
                "total_time_s": total_time_s,
            },
            "coverage": coverage_data,
        }

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all available report files in the project reports directory."""
        # Ensure standard consolidated report exists if runs or requirements exist
        if not (self.reports_dir / "consolidated_test_report.md").is_file():
            try:
                self.generate_consolidated_report()
            except Exception as exc:
                logger.debug("Deferred consolidated report creation: %s", exc)

        results: List[Dict[str, Any]] = []
        title_map = {
            "development_plan": "Development Plan",
            "consolidated_test_report": "Consolidated Test Report",
            "consolidated_report": "Consolidated Quality Report",
            "test_report": "Test Execution Report",
            "bug_report": "Bug Reports Summary",
        }

        for p in self.reports_dir.glob("*.md"):
            clean_stem = p.stem
            mtime = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()
            results.append(
                {
                    "name": clean_stem,
                    "title": title_map.get(clean_stem, clean_stem.replace("_", " ").title()),
                    "type": "markdown",
                    "generated_at": mtime,
                    "file_size": p.stat().st_size,
                }
            )

        # Sort so consolidated comes first
        results.sort(key=lambda r: 0 if "consolidated" in r["name"] else 1)
        return results
