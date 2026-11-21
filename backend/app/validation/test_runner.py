"""
Test runner for Ojas projects.
Executes pytest in a project workspace subprocess and parses JUnit XML results.
"""

import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Base workspace directory (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_WORKSPACE_DIR = _PROJECT_ROOT / "workspace"


@dataclass
class TestCaseResult:
    """Individual test execution result parsed from pytest/JUnit."""

    __test__ = False

    name: str
    classname: str = ""
    file_path: str = ""
    tc_id: str = ""
    result: str = "passed"  # "passed" | "failed" | "error" | "skipped"
    duration_ms: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None


@dataclass
class TestRunResult:
    """Consolidated results of a pytest execution run."""

    __test__ = False

    success: bool
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_ms: int = 0
    results: List[TestCaseResult] = field(default_factory=list)
    summary: str = ""


class TestRunner:
    """
    Subprocess runner for pytest inside project workspace directories.
    Produces structured test results and JUnit XML breakdown.
    """

    __test__ = False

    def __init__(self, workspace_base: Optional[Path] = None) -> None:
        self.workspace_base = workspace_base or _DEFAULT_WORKSPACE_DIR

    def get_workspace_path(self, project_id: str) -> Path:
        """Resolve workspace directory path for a project."""
        return self.workspace_base / project_id

    def find_test_files(self, workspace_path: Path) -> List[Path]:
        """Scan workspace for test files (test_*.py or *_test.py)."""
        if not workspace_path.exists():
            return []
        test_files = list(workspace_path.glob("**/test_*.py"))
        test_files.extend([f for f in workspace_path.glob("**/*_test.py") if f not in test_files])
        return test_files

    def parse_junit_xml(self, xml_path: Path) -> List[TestCaseResult]:
        """
        Parse JUnit XML report produced by `pytest --junitxml=...`.
        Extracts test case names, durations, failure/error messages.
        """
        results: List[TestCaseResult] = []
        if not xml_path.exists():
            return results

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Root can be <testsuites> or <testsuite>
            testcases = root.findall(".//testcase")
            for tc in testcases:
                name = tc.get("name", "unknown")
                classname = tc.get("classname", "")
                time_sec = float(tc.get("time", "0.0") or 0.0)
                duration_ms = int(time_sec * 1000)
                file_attr = tc.get("file", "")

                failure = tc.find("failure")
                error = tc.find("error")
                skipped = tc.find("skipped")
                system_out = tc.find("system-out")
                system_err = tc.find("system-err")

                stdout_text = system_out.text if system_out is not None and system_out.text else ""
                stderr_text = system_err.text if system_err is not None and system_err.text else ""

                if failure is not None:
                    status = "failed"
                    err_msg = failure.get("message") or failure.text or "Assertion failed"
                elif error is not None:
                    status = "error"
                    err_msg = error.get("message") or error.text or "Execution error"
                elif skipped is not None:
                    status = "skipped"
                    err_msg = skipped.get("message") or "Test skipped"
                else:
                    status = "passed"
                    err_msg = None

                results.append(
                    TestCaseResult(
                        name=name,
                        classname=classname,
                        file_path=file_attr,
                        result=status,
                        duration_ms=duration_ms,
                        stdout=stdout_text.strip(),
                        stderr=stderr_text.strip(),
                        error_message=err_msg.strip() if err_msg else None,
                    )
                )
        except Exception as exc:
            logger.warning("Failed to parse JUnit XML %s: %s", xml_path, exc)

        return results

    def run_tests(
        self,
        project_id: str,
        test_timeout: int = 60,
        test_file: Optional[str] = None,
    ) -> TestRunResult:
        """
        Execute pytest in the project workspace directory.
        Returns a structured TestRunResult.
        """
        workspace_path = self.get_workspace_path(project_id)
        if not workspace_path.exists():
            return TestRunResult(
                success=False,
                summary=f"Workspace for project {project_id} does not exist.",
            )

        test_files = self.find_test_files(workspace_path)
        if not test_files and not test_file:
            return TestRunResult(
                success=True,
                total=0,
                summary="No test files found in project workspace.",
            )

        xml_report_path = workspace_path / "result.xml"
        if xml_report_path.exists():
            try:
                xml_report_path.unlink()
            except OSError:
                pass

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--tb=short",
            f"--junitxml={xml_report_path.name}",
            "-v",
        ]
        if test_file:
            cmd.append(test_file)

        env = os.environ.copy()
        # Set PYTHONPATH so workspace code imports cleanly
        pythonpath = str(workspace_path)
        if "PYTHONPATH" in env:
            pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = pythonpath

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace_path),
                env=env,
                timeout=test_timeout,
                capture_output=True,
                text=True,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired:
            return TestRunResult(
                success=False,
                summary=f"Test execution timed out after {test_timeout} seconds.",
            )
        except Exception as exc:
            return TestRunResult(
                success=False,
                summary=f"Failed to execute pytest subprocess: {exc}",
            )

        # Parse the generated JUnit XML
        results = self.parse_junit_xml(xml_report_path)

        # Clean up result.xml if created
        if xml_report_path.exists():
            try:
                xml_report_path.unlink()
            except OSError:
                pass

        # If JUnit XML could not be parsed but tests were executed, fallback to stdout parsing
        if not results and proc.returncode != 0:
            fallback_res = TestCaseResult(
                name="test_execution_failure",
                result="failed" if proc.returncode in (1, 2) else "error",
                stdout=stdout,
                stderr=stderr,
                error_message=stderr or stdout or f"pytest exited with code {proc.returncode}",
            )
            results.append(fallback_res)

        passed = sum(1 for r in results if r.result == "passed")
        failed = sum(1 for r in results if r.result == "failed")
        errors = sum(1 for r in results if r.result == "error")
        skipped = sum(1 for r in results if r.result == "skipped")
        total = len(results)
        total_duration = sum(r.duration_ms for r in results)

        success = (failed == 0 and errors == 0 and total > 0) or (total == 0 and proc.returncode == 0)
        summary = f"{passed} passed, {failed} failed, {errors} errors, {skipped} skipped in {total_duration}ms"

        return TestRunResult(
            success=success,
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_ms=total_duration,
            results=results,
            summary=summary,
        )
