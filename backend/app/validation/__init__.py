"""
Validation package for Ojas: Static checks (AST, ruff) and test execution.
"""

from backend.app.validation.static_check import check_file, check_lint, check_syntax

__all__ = ["check_syntax", "check_lint", "check_file"]
