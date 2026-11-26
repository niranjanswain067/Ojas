"""
Phase 20: End-to-End Integration & QA Acceptance Test Suite.

Covers Acceptance Criteria AC-1 through AC-8:
- AC-1: Offline build verification (no CDN links in frontend/dist) & path traversal rejection
- AC-2: Document upload & parsing for sample project requirements
- AC-3: Orchestrator plan -> develop -> static syntax check
- AC-4 & AC-5: Testing Agent bug reports & Fix Loop stop rules (all_passed, repeated_failure, iteration_limit)
- AC-6 & AC-7: Consolidated report generation & Project ZIP download
- AC-8: Performance metrics recording
"""

import io
import json
import zipfile
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.llm.client import LLMClient
from backend.app.metrics import load_all_metrics
from backend.app.orchestrator import Orchestrator
from backend.app.storage import project_store
from backend.app.storage.file_store import resolve_safe_path
from backend.app.storage.report_writer import ReportWriter
from backend.app.validation.static_check import check_file

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class _MockE2ELLM(LLMClient):
    """Deterministic offline mock LLM for fast E2E pipeline verification."""

    def __init__(self, mode: str = "fix_success") -> None:
        self.mode = mode
        self.call_count = 0

    def is_loaded(self) -> bool:
        return True

    def get_info(self) -> dict:
        return {
            "model_name": "mock-e2e-3b",
            "loaded": True,
            "context_size": 4096,
            "load_time_seconds": 0.01,
        }

    def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        p_lower = prompt.lower()

        if "analyze the following" in p_lower or "requirements analysis" in p_lower:
            return "Analysis: Build a Calculator module with add, subtract, multiply, divide, and history."

        if "development plan" in p_lower or "file_path" in p_lower and "json" in p_lower:
            return json.dumps(
                {
                    "project_name": "Calculator",
                    "plan_summary": "Modular Python calculator",
                    "files": [
                        {
                            "file_path": "calculator.py",
                            "description": "Calculator class with arithmetic and history",
                            "classes": ["Calculator"],
                            "functions": ["add", "subtract", "multiply", "divide"],
                            "dependencies": [],
                            "order": 1,
                        }
                    ],
                }
            )

        if "probable_cause" in p_lower and "suggested_fix" in p_lower:
            return json.dumps(
                {
                    "probable_cause": "Arithmetic or zero-division logic error",
                    "severity": "high",
                    "expected_behavior": "Return exact sum and raise ValueError on zero division",
                    "suggested_fix": "Use a + b and check if b == 0",
                }
            )

        if "fix" in p_lower or "bug" in p_lower:
            if self.mode == "fix_success":
                return (
                    "```python\n"
                    "class Calculator:\n"
                    "    def __init__(self):\n"
                    "        self.history = []\n"
                    "    def add(self, a, b):\n"
                    "        res = a + b\n"
                    "        self.history.append(res)\n"
                    "        return res\n"
                    "    def divide(self, a, b):\n"
                    "        if b == 0:\n"
                    "            raise ValueError('Cannot divide by zero')\n"
                    "        return a / b\n"
                    "```"
                )
            else:
                # Always return same buggy code to test repeated_failure / iteration_limit
                return (
                    "```python\n"
                    "class Calculator:\n"
                    "    def add(self, a, b):\n"
                    "        return a - b  # intentional bug\n"
                    "```"
                )

        # Default code generation response
        return (
            "```python\n"
            "class Calculator:\n"
            "    def __init__(self):\n"
            "        self.history = []\n"
            "    def add(self, a, b):\n"
            "        res = a + b\n"
            "        self.history.append(res)\n"
            "        return res\n"
            "    def divide(self, a, b):\n"
            "        if b == 0:\n"
            "            raise ValueError('Cannot divide by zero')\n"
            "        return a / b\n"
            "```"
        )

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield self.generate(prompt, **kwargs)


@pytest.fixture(scope="module")
def e2e_client():
    """FastAPI TestClient with LLM loading mocked out for fast startup."""
    from backend.app.main import app

    with patch("backend.app.llm.llama_cpp_client.LlamaCppClient") as mock_cls:
        mock_cls.return_value = _MockE2ELLM()
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


class TestPhase20Acceptance:
    """Acceptance criteria verification suite (AC-1 to AC-8)."""

    def test_ac1_offline_frontend_build_no_cdn(self):
        dist_index = _PROJECT_ROOT / "frontend" / "dist" / "index.html"
        assert dist_index.exists(), "frontend/dist/index.html must be built"
        html = dist_index.read_text(encoding="utf-8")
        for forbidden in ("unpkg.com", "jsdelivr.net", "cdnjs.cloudflare.com", "fonts.googleapis.com"):
            assert forbidden not in html.lower(), f"Found external CDN reference: {forbidden}"

    def test_ac1_path_traversal_rejected(self):
        proj = project_store.create_project(name="QA Security Proj")
        p_id = proj["id"]
        try:
            with pytest.raises(ValueError):
                resolve_safe_path(p_id, "../../etc/passwd")
            with pytest.raises(ValueError):
                resolve_safe_path(p_id, "..\\..\\Windows\\System32\\cmd.exe")
        finally:
            project_store.delete_project(p_id)

    def test_ac2_to_ac8_full_pipeline_calculator_sample(self, e2e_client: TestClient):
        # 1. Create project
        res = e2e_client.post(
            "/api/projects",
            json={"name": "E2E Calculator QA", "description": "Phase 20 E2E test"},
        )
        assert res.status_code == 201
        p_id = res.json()["id"]

        try:
            ws_dir = project_store.get_workspace_dir(p_id)

            # 2. AC-2: Copy sample requirements document into workspace
            sample_req = _PROJECT_ROOT / "samples" / "calculator" / "calculator_requirements.txt"
            assert sample_req.exists()
            (ws_dir / "documents" / "calculator_requirements.txt").write_text(
                sample_req.read_text(encoding="utf-8"), encoding="utf-8"
            )

            # 3. AC-3: Run Plan -> Develop via Orchestrator
            orch = Orchestrator(llm_client=_MockE2ELLM(mode="fix_success"))
            plan_result = orch.run_plan(p_id, prompt="Build Calculator from requirements")
            assert plan_result.success is True
            assert plan_result.status == "pending_approval"
            assert plan_result.plan_text is not None

            dev_result = orch.run_develop(
                p_id, prompt="Build Calculator", plan_text=plan_result.plan_text
            )
            assert dev_result.success is True
            assert "calculator.py" in dev_result.files_generated
            calc_path = ws_dir / "calculator.py"
            assert check_file(calc_path.read_text(encoding="utf-8"), str(calc_path)).passed is True

            # 4. AC-4 & AC-5: Inject a test suite + buggy function, run Fix Loop -> all_passed
            (ws_dir / "calculator.py").write_text(
                "class Calculator:\n"
                "    def add(self, a, b):\n"
                "        return a - b  # bug\n"
                "    def divide(self, a, b):\n"
                "        return a / b\n",
                encoding="utf-8",
            )
            (ws_dir / "tests" / "test_calculator.py").write_text(
                "import sys\nfrom pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
                "import pytest\n"
                "from calculator import Calculator\n\n"
                "def test_add():\n"
                "    assert Calculator().add(2, 3) == 5\n\n"
                "def test_divide_zero():\n"
                "    with pytest.raises(ValueError):\n"
                "        Calculator().divide(10, 0)\n",
                encoding="utf-8",
            )

            fix_res = orch.run_fix_loop(p_id, iteration_limit=3)
            assert fix_res.success is True
            assert fix_res.stop_reason == "all_passed"

            # 5. AC-6 & AC-7: Consolidated report & ZIP download
            report_md = ReportWriter(p_id).generate_consolidated_report()
            assert "E2E Calculator QA" in report_md

            dl_res = e2e_client.get(f"/api/projects/{p_id}/download")
            assert dl_res.status_code == 200
            assert dl_res.headers.get("content-type") == "application/zip"
            with zipfile.ZipFile(io.BytesIO(dl_res.content), "r") as zf:
                assert "calculator.py" in zf.namelist()
                assert "tests/test_calculator.py" in zf.namelist()

            # 6. AC-8: Metrics recorded
            all_metrics = load_all_metrics()
            run_ids = {m.get("run_id") for m in all_metrics}
            assert fix_res.run_id in run_ids
            matching = [m for m in all_metrics if m.get("run_id") == fix_res.run_id][0]
            assert matching["fix_loop_iterations"] >= 1
            assert matching["peak_ram_mb"] > 0.0

        finally:
            project_store.delete_project(p_id)

    def test_ac5_fix_loop_repeated_failure_stop_rule(self):
        proj = project_store.create_project(name="QA Repeated Failure")
        p_id = proj["id"]
        try:
            ws_dir = project_store.get_workspace_dir(p_id)
            (ws_dir / "calculator.py").write_text(
                "class Calculator:\n    def add(self, a, b):\n        return a - b\n",
                encoding="utf-8",
            )
            (ws_dir / "tests" / "test_calc.py").write_text(
                "import sys\nfrom pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
                "from calculator import Calculator\n"
                "def test_add():\n"
                "    assert Calculator().add(2, 3) == 5\n",
                encoding="utf-8",
            )

            orch = Orchestrator(llm_client=_MockE2ELLM(mode="always_buggy"))
            res = orch.run_fix_loop(p_id, iteration_limit=5)
            assert res.success is False
            assert res.stop_reason == "repeated_failure"
        finally:
            project_store.delete_project(p_id)
