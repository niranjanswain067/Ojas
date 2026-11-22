"""
Unit tests for backend.app.agents.testing_agent
"""

import json
import uuid
from typing import Iterator, List, Optional

from backend.app.agents.testing_agent import TestingAgent
from backend.app.llm.client import LLMClient
from backend.app.storage.db import init_database
from backend.app.storage.document_store import ensure_project
from backend.app.storage.file_store import write_file
from backend.app.storage.test_store import register_test_file
from backend.app.validation.test_runner import TestCaseResult


def setup_module():
    init_database()


class MockLLM(LLMClient):
    def __init__(self, responses: Optional[List[str]] = None) -> None:
        self.responses = list(responses or [])

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> str:
        if self.responses:
            return self.responses.pop(0)
        return json.dumps({
            "probable_cause": "Calculation off-by-one error",
            "severity": "high",
            "expected_behavior": "Should return exact sum",
            "suggested_fix": "Change + 1 to + 0",
        })

    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> Iterator[str]:
        yield self.generate(prompt)

    def is_loaded(self) -> bool:
        return True

    def get_info(self) -> dict:
        return {"model_name": "mock"}


def test_extract_json_block():
    agent = TestingAgent()
    text = 'Some prefix ```json\n{"key": "value"}\n``` suffix'
    assert agent._extract_json_block(text) == '{"key": "value"}'

    plain = '{"key2": "value2"}'
    assert agent._extract_json_block(plain) == '{"key2": "value2"}'


def test_analyze_failures_with_llm():
    project_id = str(uuid.uuid4())
    ensure_project(project_id)
    mock_llm = MockLLM()
    agent = TestingAgent(llm_client=mock_llm, project_id=project_id)

    # Create workspace files
    write_file(project_id, "calculator.py", "def add(a, b): return a + b + 1")
    write_file(project_id, "tests/test_calc.py", "def test_add(): assert add(1, 2) == 3")
    register_test_file(project_id, "tests/test_calc.py", "def test_add(): assert add(1, 2) == 3")

    failed_tc = TestCaseResult(
        name="test_add",
        file_path="tests/test_calc.py",
        result="failed",
        duration_ms=50,
        error_message="AssertionError: assert 4 == 3",
    )

    reports = agent.analyze_failures([failed_tc], project_id=project_id, run_id="run-1", iteration=1)
    assert len(reports) == 1
    rep = reports[0]
    assert rep["bug_id"] == "B-001"
    assert rep["severity"] == "high"
    assert "Calculation off-by-one" in rep["probable_cause"]


def test_analyze_failures_fallback_without_llm():
    project_id = str(uuid.uuid4())
    agent = TestingAgent(llm_client=None, project_id=project_id)

    failed_tc = TestCaseResult(
        name="test_missing_value",
        file_path="service.py",
        result="failed",
        error_message="KeyError: 'user_id' not found in payload",
    )

    reports = agent.analyze_failures([failed_tc], project_id=project_id, run_id="run-2", iteration=0)
    assert len(reports) == 1
    rep = reports[0]
    assert rep["bug_id"] == "B-001"
    assert "KeyError" in rep["probable_cause"]
