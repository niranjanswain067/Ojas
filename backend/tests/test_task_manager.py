"""
Unit tests for TaskManager (Phase 12).
"""

import threading
import time
import pytest

from backend.app.tasks.task_manager import TaskManager, TaskStatus


@pytest.fixture
def tm():
    """Create a fresh TaskManager instance for each test."""
    manager = TaskManager(max_workers=1)
    yield manager
    manager.reset()


def test_submit_and_complete(tm: TaskManager):
    """Task should run in background and complete successfully."""
    completed = threading.Event()

    def work():
        time.sleep(0.05)
        completed.set()

    accepted = tm.submit(work, run_id="run-1")
    assert accepted is True
    assert tm.is_busy() is True
    assert tm.get_status("run-1") == TaskStatus.RUNNING

    # Wait for completion
    assert completed.wait(timeout=2.0) is True
    time.sleep(0.05)  # brief grace period for wrapper to mark completed

    assert tm.is_busy() is False
    assert tm.get_status("run-1") == TaskStatus.COMPLETED

    info = tm.get_task_info("run-1")
    assert info is not None
    assert info["status"] == "completed"
    assert info["error"] is None
    assert info["duration_seconds"] > 0


def test_reject_second_task_when_busy(tm: TaskManager):
    """Submitting a second task while busy must return False."""
    release_first = threading.Event()

    def long_task():
        release_first.wait(timeout=2.0)

    accepted1 = tm.submit(long_task, run_id="run-1")
    assert accepted1 is True
    assert tm.is_busy() is True

    # Attempt to submit second task
    accepted2 = tm.submit(lambda: None, run_id="run-2")
    assert accepted2 is False
    assert tm.get_status("run-2") is None

    # Unblock first task
    release_first.set()
    time.sleep(0.05)
    assert tm.is_busy() is False


def test_cancel_task(tm: TaskManager):
    """Cancelling a running task should set cancel event and mark status cancelled."""
    started = threading.Event()

    def stoppable(cancel_event: threading.Event):
        started.set()
        while not cancel_event.is_set():
            time.sleep(0.01)

    tm.submit(stoppable, run_id="run-cancel")
    assert started.wait(timeout=2.0) is True

    assert tm.is_busy() is True
    cancelled = tm.cancel("run-cancel")
    assert cancelled is True

    # Wait for task to notice cancellation and finish
    time.sleep(0.1)
    assert tm.is_busy() is False
    assert tm.get_status("run-cancel") == TaskStatus.CANCELLED
    assert tm.is_cancelled("run-cancel") is True


def test_task_failure_records_error(tm: TaskManager):
    """If task raises an exception, status should be failed and error recorded."""
    def failing_task():
        raise ValueError("Simulated failure in test task")

    tm.submit(failing_task, run_id="run-fail")
    time.sleep(0.1)

    assert tm.is_busy() is False
    assert tm.get_status("run-fail") == TaskStatus.FAILED
    info = tm.get_task_info("run-fail")
    assert info is not None
    assert "Simulated failure in test task" in (info["error"] or "")

