"""
Integration tests for SSE stream, run status and run cancellation (Phase 12).
"""

import threading
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.events.event_bus import get_event_bus
from backend.app.main import app
from backend.app.tasks.task_manager import get_task_manager


@pytest.fixture(scope="module")
def client():
    """Start the FastAPI app with TestClient."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_tasks_and_events():
    """Reset TaskManager and EventBus before each test."""
    tm = get_task_manager()
    bus = get_event_bus()
    tm.reset()
    bus.clear()
    yield
    tm.reset()
    bus.clear()


def test_get_run_status_not_found(client: TestClient):
    """Querying status of unknown run should return 404."""
    res = client.get("/api/runs/non-existent-run/status")
    assert res.status_code == 404


def test_submit_and_get_run_status(client: TestClient):
    """Running task should report status in /api/runs/{run_id}/status."""
    tm = get_task_manager()
    hold_event = threading.Event()

    def background_work():
        hold_event.wait(timeout=2.0)

    tm.submit(background_work, run_id="run-status-test")
    res = client.get("/api/runs/run-status-test/status")
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "run-status-test"
    assert data["status"] == "running"
    assert data["is_busy"] is True

    # Finish task
    hold_event.set()
    time.sleep(0.05)

    res_done = client.get("/api/runs/run-status-test/status")
    assert res_done.status_code == 200
    assert res_done.json()["status"] == "completed"
    assert res_done.json()["is_busy"] is False


def test_cancel_active_run(client: TestClient):
    """POST /api/runs/{run_id}/cancel should cancel active run."""
    tm = get_task_manager()
    started = threading.Event()

    def stoppable(cancel_event: threading.Event):
        started.set()
        while not cancel_event.is_set():
            time.sleep(0.01)

    tm.submit(stoppable, run_id="run-to-cancel")
    assert started.wait(timeout=2.0) is True

    res = client.post("/api/runs/run-to-cancel/cancel")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

    time.sleep(0.05)
    assert tm.is_busy() is False


def test_sse_event_stream(client: TestClient):
    """SSE endpoint should deliver initial handshake and published events."""
    run_id = "run-sse-stream"
    bus = get_event_bus()

    # Pre-populate an event
    bus.publish(run_id, "stage", {"stage": "planning", "status": "started"})
    bus.publish(run_id, "done", {"status": "completed"})

    # Connect with TestClient streaming
    with client.stream("GET", f"/api/runs/{run_id}/events") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line)
            if "event: done" in line:
                break

        full_stream = "\n".join(lines)
        assert "event: connected" in full_stream
        assert "event: stage" in full_stream
        assert "event: done" in full_stream

