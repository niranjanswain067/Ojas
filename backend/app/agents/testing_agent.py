"""
Testing Agent for Ojas.
Performs intelligent test failure diagnosis, requirement mapping, and structured bug report generation.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.llm.client import LLMClient
from backend.app.storage.bug_store import get_next_bug_id, save_bug_report
from backend.app.storage.file_store import read_file
from backend.app.storage.test_store import get_test_case_by_name_or_function, get_test_case_by_tc_id
from backend.app.validation.test_runner import TestCaseResult

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _read_template(template_name: str) -> str:
    """Read a prompt template file from backend/app/agents/prompts/."""
    path = _PROMPTS_DIR / template_name
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


class TestingAgent:
    """
    Intelligent test failure analyzer.
    Maps failed tests to requirements and implementation code,
    interrogates LLM for root cause and severity, and outputs structured BugReports.
    """

    __test__ = False

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        search_engine: Optional[Any] = None,
        project_id: str = "",
    ) -> None:
        self.llm_client = llm_client
        self.search_engine = search_engine
        self.project_id = project_id

    def _extract_json_block(self, text: str) -> str:
        """Extract JSON substring from triple backtick or outer braces."""
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1].strip()
        return text.strip()

    def _resolve_source_file_and_function(
        self,
        tc: TestCaseResult,
        project_id: str,
    ) -> tuple[Optional[str], Optional[str], str]:
        """
        Locate the implementation source file and function being tested.
        Returns (file_path, function_name, code_content).
        """
        # 1. Check if error trace references a project source file
        err = tc.error_message or ""
        out = f"{tc.stdout}\n{tc.stderr}\n{err}"

        # Look for file paths in error traceback like File ".../app.py", line 42, in my_func
        tb_matches = re.findall(r'File "([^"]+\.py)", line (\d+)(?:, in (\w+))?', out)
        for path_str, line_no, func in reversed(tb_matches):
            p = Path(path_str)
            filename = p.name
            if not filename.startswith("test_") and not filename.endswith("_test.py"):
                # Candidate source file
                try:
                    res = read_file(project_id, filename)
                    content = res.content if hasattr(res, "content") else str(res)
                    return filename, func or None, content
                except Exception:
                    pass

        # 2. Derive source filename from test filename (e.g. test_calculator.py -> calculator.py)
        if tc.file_path:
            test_stem = Path(tc.file_path).stem
            source_stem = re.sub(r"^test_", "", test_stem)
            source_stem = re.sub(r"_test$", "", source_stem)
            candidate = f"{source_stem}.py"
            try:
                res = read_file(project_id, candidate)
                content = res.content if hasattr(res, "content") else str(res)
                func_name = tc.name.replace("test_", "") if tc.name.startswith("test_") else tc.name
                return candidate, func_name, content
            except Exception:
                pass

        # 3. Fallback: return test file itself
        if tc.file_path:
            try:
                res = read_file(project_id, tc.file_path)
                content = res.content if hasattr(res, "content") else str(res)
                return tc.file_path, tc.name, content
            except Exception:
                pass

        return None, tc.name, ""

    def _resolve_requirement(
        self,
        project_id: str,
        tc_record: Optional[Dict[str, Any]],
        func_name: Optional[str],
    ) -> tuple[Optional[str], str]:
        """
        Find linked requirement ID and description.
        Returns (req_id, requirement_text).
        """
        if tc_record and tc_record.get("linked_req_ids"):
            req_id = tc_record["linked_req_ids"][0]
            # Try to fetch text from document store or DB
            try:
                from backend.app.storage.document_store import get_document_chunks

                chunks = get_document_chunks(project_id)
                for chunk in chunks:
                    if req_id.upper() in (chunk.get("req_ids") or []):
                        return req_id, chunk.get("content", f"Requirement {req_id}")
            except Exception:
                pass
            return req_id, f"Requirement specification {req_id}"

        # If search engine is available, query by function name
        if self.search_engine and func_name:
            try:
                hits = self.search_engine.search_requirements(func_name, limit=1)
                if hits:
                    best = hits[0]
                    rid = best.get("req_id")
                    return rid, best.get("content", f"Requirement {rid}")
            except Exception:
                pass

        return None, "Verify component functionality according to expected specifications."

    def analyze_failures(
        self,
        test_results: List[TestCaseResult],
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        iteration: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Analyze all failed or errored test cases and produce structured BugReports.
        """
        proj_id = project_id or self.project_id
        r_id = run_id or "run-test"
        failures = [t for t in test_results if t.result in ("failed", "error")]
        reports: List[Dict[str, Any]] = []

        template = _read_template("bug_analysis.txt")

        for tc in failures:
            # Look up test case in DB if registered
            tc_record = get_test_case_by_name_or_function(proj_id, tc.name)
            tc_id = tc.tc_id or (tc_record.get("tc_id") if tc_record else "")

            # Resolve implementation code and target function
            source_file, target_func, code_content = self._resolve_source_file_and_function(tc, proj_id)

            # Resolve linked requirement
            req_id, req_text = self._resolve_requirement(proj_id, tc_record, target_func)

            err_msg = tc.error_message or tc.stderr or tc.stdout or "Test assertion failure"

            # Prepare bug fields
            probable_cause = ""
            severity = "high" if "AssertionError" in err_msg or "Error" in err_msg else "medium"
            expected_behavior = "Function should return expected output without raising errors."
            suggested_fix = "Update implementation logic to satisfy assertions."

            # If LLM is available, consult model
            if self.llm_client and self.llm_client.is_loaded():
                try:
                    prompt = template.format(
                        requirement_text=req_text,
                        code_chunk=code_content[:1500] if code_content else "(Source code unavailable)",
                        test_name=tc.name,
                        tc_id=tc_id or "N/A",
                        error_message=err_msg[:1200],
                    )
                    raw_resp = self.llm_client.generate(prompt=prompt, max_tokens=512, temperature=0.1)
                    parsed = json.loads(self._extract_json_block(raw_resp))

                    probable_cause = parsed.get("probable_cause", "")
                    severity = parsed.get("severity", severity).lower()
                    if severity not in ("critical", "high", "medium", "low"):
                        severity = "medium"
                    expected_behavior = parsed.get("expected_behavior", expected_behavior)
                    suggested_fix = parsed.get("suggested_fix", suggested_fix)
                except Exception as exc:
                    logger.warning("LLM bug analysis failed for %s: %s", tc.name, exc)

            if not probable_cause:
                # Deterministic fallback from error trace
                first_lines = [l.strip() for l in err_msg.splitlines() if l.strip() and not l.strip().startswith("Traceback")]
                probable_cause = " | ".join(first_lines[-2:]) if first_lines else "Test assertion failed."

            bug_id = get_next_bug_id(proj_id)

            report = save_bug_report(
                project_id=proj_id,
                run_id=r_id,
                bug_id=bug_id,
                expected_result=expected_behavior,
                actual_result=err_msg[:500],
                req_id=req_id,
                tc_id=tc_id or None,
                file_path=source_file or tc.file_path or None,
                function_name=target_func,
                severity=severity,
                probable_cause=probable_cause,
                iteration=iteration,
                status="open",
                fix_description=suggested_fix,
            )
            reports.append(report)

        return reports
