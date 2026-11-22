"""
Unit tests for fix loop execution and the 3 mandatory stopping conditions in Orchestrator.
"""

import json
import uuid
from typing import Iterator, List, Optional
from unittest.mock import MagicMock, patch

from backend.app.events.event_bus import EventBus
from backend.app.llm.client import LLMClient
from backend.app.orchestrator import Orchestrator, RunResult
from backend.app.storage.db import init_database
from backend.app.storage.file_store import write_file
from backend.app.tasks.task_manager import TaskManager
from backend.app.validation.test_runner import TestCaseResult, TestRunResult


def setup_module():
    init_database()


class MockLLM(LLMClient):
    def __init__(self, responses: Optional[List[str]] = None) -> None:
        self.responses = list(responses or [])

    def generate(self, prompt: str, **kwargs) -> str:
        if self.responses:
            return self.responses.pop(0)
        return """
```python
def calculate(a: int, b: int) -> int:
    return a + b
```
"""

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield self.generate(prompt)

    def is_loaded(self) -> bool:
        return True

    def get_info(self) -> dict:
        return {"model_name": "mock"}


def test_fix_loop_stop_rule_1_all_tests_pass():
    """Stopping rule 1: stops immediately with stop_reason='all_passed' when all tests pass."""
    project_id = str(uuid.uuid4())
    mock_llm = MockLLM()
    event_bus = EventBus()
    task_mgr = TaskManager()

    orchestrator = Orchestrator(llm_client=mock_llm, task_manager=task_mgr, event_bus=event_bus)

    # Mock TestRunner to return passed test result on first iteration
    with patch("backend.app.orchestrator.TestRunner") as MockRunner:
        instance = MockRunner.return_value
        instance.run_tests.return_value = TestRunResult(
            success=True,
            total=1,
            passed=1,
            failed=0,
            summary="1 passed in 10ms",
            results=[TestCaseResult(name="test_ok", result="passed", duration_ms=10)],
        )

        res = orchestrator.run_fix_loop(project_id, iteration_limit=5)
        assert res.success is True
        assert res.stop_reason == "all_passed"
        assert res.status == "completed"


def test_fix_loop_stop_rule_2_repeated_failure():
    """Stopping rule 2: stops with stop_reason='repeated_failure' when identical failure repeats."""
    project_id = str(uuid.uuid4())
    mock_llm = MockLLM()
    event_bus = EventBus()
    task_mgr = TaskManager()

    orchestrator = Orchestrator(llm_client=mock_llm, task_manager=task_mgr, event_bus=event_bus)

    # Mock TestRunner to return the exact same failure twice
    with patch("backend.app.orchestrator.TestRunner") as MockRunner:
        instance = MockRunner.return_value
        failed_res = TestRunResult(
            success=False,
            total=1,
            failed=1,
            summary="1 failed in 20ms",
            results=[TestCaseResult(name="test_broken", result="failed", error_message="AssertionError: 1 != 2")],
        )
        instance.run_tests.return_value = failed_res

        res = orchestrator.run_fix_loop(project_id, iteration_limit=5)
        assert res.success is False
        assert res.stop_reason == "repeated_failure"
        assert res.status == "failed"
        assert "repeated" in res.message


def test_fix_loop_stop_rule_3_iteration_limit():
    """Stopping rule 3: stops with stop_reason='iteration_limit' when max iterations reached without all passing."""
    project_id = str(uuid.uuid4())
    mock_llm = MockLLM()
    event_bus = EventBus()
    task_mgr = TaskManager()

    orchestrator = Orchestrator(llm_client=mock_llm, task_manager=task_mgr, event_bus=event_bus)

    # Mock TestRunner to return different failures each iteration so repeated_failure doesn't trigger early
    with patch("backend.app.orchestrator.TestRunner") as MockRunner:
        instance = MockRunner.return_value

        def dynamic_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return TestRunResult(
                success=False,
                total=1,
                failed=1,
                summary="1 failed",
                results=[TestCaseResult(name="test_varying", result="failed", error_message=f"Error code {call_count}")],
            )

        call_count = 0
        instance.run_tests.side_effect = dynamic_failures

        res = orchestrator.run_fix_loop(project_id, iteration_limit=3)
        assert res.success is False
        assert res.stop_reason == "iteration_limit"
        assert res.status == "failed"
        assert call_count == 3


def test_fix_loop_cancellation():
    """Cooperative cancellation stops fix loop cleanly with stop_reason='user_cancelled'."""
    import threading

    project_id = str(uuid.uuid4())
    mock_llm = MockLLM()
    event_bus = EventBus()
    task_mgr = TaskManager()

    run_id = str(uuid.uuid4())
    ev = threading.Event()
    ev.set()
    task_mgr._cancel_events[run_id] = ev

    orchestrator = Orchestrator(llm_client=mock_llm, task_manager=task_mgr, event_bus=event_bus)
    res = orchestrator.run_fix_loop(project_id, iteration_limit=5, run_id=run_id)

    assert res.success is False
    assert res.stop_reason == "user_cancelled"
    assert res.status == "cancelled"


def test_orchestrator_run_test():
    """Verify run_test executes TestRunner, records results, and returns RunResult."""
    project_id = str(uuid.uuid4())
    mock_llm = MockLLM()
    event_bus = EventBus()
    task_mgr = TaskManager()

    orchestrator = Orchestrator(llm_client=mock_llm, task_manager=task_mgr, event_bus=event_bus)

    with patch("backend.app.orchestrator.TestRunner") as MockRunner:
        instance = MockRunner.return_value
        instance.run_tests.return_value = TestRunResult(
            success=True,
            total=2,
            passed=2,
            failed=0,
            summary="2 passed in 15ms",
            results=[
                TestCaseResult(name="test_1", result="passed", duration_ms=5),
                TestCaseResult(name="test_2", result="passed", duration_ms=10),
            ],
        )

        res = orchestrator.run_test(project_id)
        assert res.success is True
        assert res.status == "completed"
        assert res.stop_reason == "all_passed"
