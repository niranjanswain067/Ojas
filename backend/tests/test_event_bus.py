"""
Unit tests for EventBus (Phase 12).
"""

import asyncio
import threading
import time
import pytest

from backend.app.events.event_bus import EventBus


@pytest.fixture
def bus():
    """Create a fresh EventBus instance."""
    event_bus = EventBus()
    yield event_bus
    event_bus.clear()


@pytest.mark.anyio
async def test_publish_and_subscribe(bus: EventBus):
    """Subscribers should receive published events in order."""
    run_id = "run-test-1"
    received = []

    async def reader():
        async for event in bus.subscribe(run_id, replay_history=False):
            received.append(event)
            if event["event_type"] == "done":
                break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.02)  # allow subscriber to register

    bus.publish(run_id, "stage", {"stage": "generating", "status": "started"})
    bus.publish(run_id, "file", {"path": "app/models.py", "action": "created"})
    bus.publish(run_id, "done", {"status": "completed"})

    await asyncio.wait_for(task, timeout=2.0)

    assert len(received) == 3
    assert received[0]["event_type"] == "stage"
    assert received[0]["data"]["stage"] == "generating"
    assert received[1]["event_type"] == "file"
    assert received[2]["event_type"] == "done"


@pytest.mark.anyio
async def test_thread_safe_publish(bus: EventBus):
    """Events published from a synchronous worker thread should reach async subscriber."""
    run_id = "run-thread-safe"
    received = []

    async def reader():
        async for event in bus.subscribe(run_id, replay_history=False):
            received.append(event)
            if event["event_type"] == "done":
                break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.02)

    def worker_thread():
        time.sleep(0.02)
        bus.publish(run_id, "token", {"text": "def foo():"})
        bus.publish(run_id, "done", {"status": "completed"})

    thread = threading.Thread(target=worker_thread)
    thread.start()
    thread.join()

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 2
    assert received[0]["event_type"] == "token"
    assert received[1]["event_type"] == "done"


@pytest.mark.anyio
async def test_history_replay(bus: EventBus):
    """New subscriber should receive previous events when replay_history is True."""
    run_id = "run-replay"

    # Publish before subscriber exists
    bus.publish(run_id, "stage", {"stage": "planning"})
    bus.publish(run_id, "check", {"tool": "ruff", "passed": True})

    history = bus.get_history(run_id)
    assert len(history) == 2

    received = []

    async def reader():
        async for event in bus.subscribe(run_id, replay_history=True):
            received.append(event)
            if len(received) >= 2:
                break

    task = asyncio.create_task(reader())
    await asyncio.wait_for(task, timeout=2.0)

    assert len(received) == 2
    assert received[0]["event_type"] == "stage"
    assert received[1]["event_type"] == "check"


@pytest.mark.anyio
async def test_unsubscribe_cleans_up(bus: EventBus):
    """Unsubscribing or exiting generator should remove subscriber."""
    run_id = "run-cleanup"
    assert bus.get_subscriber_count(run_id) == 0

    async def short_reader():
        gen = bus.subscribe(run_id, replay_history=False)
        try:
            async for _ in gen:
                break
        finally:
            await gen.aclose()

    task = asyncio.create_task(short_reader())
    await asyncio.sleep(0.02)
    assert bus.get_subscriber_count(run_id) == 1

    bus.publish(run_id, "ping", {})
    await asyncio.wait_for(task, timeout=2.0)

    # After exit, subscriber count should return to 0
    assert bus.get_subscriber_count(run_id) == 0
