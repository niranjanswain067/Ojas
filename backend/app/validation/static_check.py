"""
Static code analysis for Ojas: AST syntax validation and Ruff lint checking.
"""

import ast
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from backend.app.schemas.development import CheckIssue, CheckResult

logger = logging.getLogger(__name__)


def _find_ruff_executable() -> Optional[list[str]]:
    """Locate the ruff executable or module invocation command."""
    ruff_path = shutil.which("ruff")
    if ruff_path:
        return [ruff_path]

    # Check python -m ruff
    try:
        res = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return [sys.executable, "-m", "ruff"]
    except Exception:
        pass

    return None


def check_syntax(code: str, file_path: str = "") -> CheckResult:
    """
    Validate Python syntax using ast.parse.

    Returns CheckResult with passed=True if valid,
    or passed=False with specific line, column, and error details.
    """
    display_path = file_path or "<string>"
    try:
        ast.parse(code, filename=display_path)
        return CheckResult(passed=True, issues=[])
    except (SyntaxError, IndentationError) as exc:
        lineno = getattr(exc, "lineno", 1) or 1
        offset = getattr(exc, "offset", 1) or 1
        msg = getattr(exc, "msg", str(exc)) or str(exc)
        code_str = "E998" if isinstance(exc, IndentationError) else "E999"
        return CheckResult(
            passed=False,
            issues=[
                CheckIssue(
                    line=lineno,
                    col=offset,
                    code=code_str,
                    message=msg,
                )
            ],
        )
    except Exception as exc:
        return CheckResult(
            passed=False,
            issues=[
                CheckIssue(
                    line=1,
                    col=1,
                    code="PARSE_ERR",
                    message=f"Failed to parse AST: {exc}",
                )
            ],
        )


def check_lint(file_path: str) -> CheckResult:
    """
    Run ruff check as a subprocess on the target file.

    Parses JSON output for issues. If ruff is not installed or available,
    logs a debug notice and returns passed=True.
    """
    ruff_cmd = _find_ruff_executable()
    if not ruff_cmd:
        logger.debug("Ruff linter not available in environment; skipping lint check.")
        return CheckResult(passed=True, issues=[])

    target = Path(file_path).resolve()
    if not target.is_file():
        logger.warning("Target file %s does not exist on disk for linting.", file_path)
        return CheckResult(passed=True, issues=[])

    cmd = ruff_cmd + ["check", "--output-format=json", str(target)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        logger.warning("Ruff lint check timed out for %s", file_path)
        return CheckResult(
            passed=False,
            issues=[CheckIssue(line=1, col=1, code="TIMEOUT", message="Ruff check timed out")],
        )
    except Exception as exc:
        logger.warning("Error running ruff lint: %s", exc)
        return CheckResult(passed=True, issues=[])

    stdout = proc.stdout.strip()
    if proc.returncode == 0 and not stdout:
        return CheckResult(passed=True, issues=[])

    issues = []
    if stdout:
        try:
            entries = json.loads(stdout)
            for item in entries:
                location = item.get("location", {})
                row = location.get("row", 1)
                column = location.get("column", 1)
                rule_code = item.get("code") or "LINT"
                msg = item.get("message") or "Lint issue"
                issues.append(
                    CheckIssue(
                        line=row,
                        col=column,
                        code=rule_code,
                        message=msg,
                    )
                )
        except json.JSONDecodeError:
            # Fallback text regex parsing
            for line in stdout.splitlines():
                match = re.match(r"^.+?:(\d+):(\d+):\s*([A-Z0-9]+)\s*(.+)$", line)
                if match:
                    issues.append(
                        CheckIssue(
                            line=int(match.group(1)),
                            col=int(match.group(2)),
                            code=match.group(3),
                            message=match.group(4).strip(),
                        )
                    )

    passed = len(issues) == 0
    return CheckResult(passed=passed, issues=issues)


def check_file(code: str, file_path: str = "") -> CheckResult:
    """
    Combined validation: Run syntax check first. If syntax fails,
    do NOT run lint. If syntax passes, run ruff linting.
    """
    syntax_res = check_syntax(code, file_path=file_path)
    if not syntax_res.passed:
        return syntax_res

    # Syntax passed; perform lint check
    if file_path and Path(file_path).is_file():
        # Target file exists on disk
        return check_lint(file_path)

    # Use a temporary file for linting
    temp_fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(code)
        lint_res = check_lint(temp_path)
        return lint_res
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
