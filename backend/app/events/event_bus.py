"""
Ojas Event Bus.

Thread-safe publish / async subscribe event bus feeding SSE streams.
Supports publishing from synchronous background worker threads and
streaming events asynchronously to FastAPI / Starlette endpoints.
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-memory pub/sub event bus partitioned by run_id.

    - publish() is thread-safe and can be called from synchronous background threads.
    - subscribe() is an async generator yielding structured event dictionaries.
    """

    def __init__(self, max_history_per_run: int = 500) -> None:
        self._lock = threading.RLock()
        # run_id -> { subscriber_id: asyncio.Queue }
        self._subscribers: Dict[str, Dict[str, asyncio.Queue]] = {}
        # subscriber_id -> asyncio.AbstractEventLoop
        self._subscriber_loops: Dict[str, asyncio.AbstractEventLoop] = {}
        # run_id -> List of event dicts
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._max_history = max_history_per_run

    def publish(self, run_id: str, event_type: str, data: Any) -> None:
        """
        Publish an event to all subscribers listening to run_id.
        Can be called from any thread (synchronous background tasks or async handlers).
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        event = {
            "run_id": run_id,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp,
        }

        with self._lock:
            # Store in history
            if run_id not in self._history:
                self._history[run_id] = []
            self._history[run_id].append(event)
            if len(self._history[run_id]) > self._max_history:
                self._history[run_id].pop(0)

            # Copy targets to avoid holding lock while dispatching
            subscribers = list(self._subscribers.get(run_id, {}).items())

        for sub_id, queue in subscribers:
            loop = self._subscriber_loops.get(sub_id)
            if loop is not None and loop.is_running():
                try:
                    # Thread-safe queue delivery across async loops
                    loop.call_soon_threadsafe(queue.put_nowait, event)
                except Exception as exc:
                    logger.warning("Failed to deliver event to subscriber %s: %s", sub_id, exc)
            else:
                try:
                    queue.put_nowait(event)
                except Exception as exc:
                    logger.warning("Failed to queue event for subscriber %s: %s", sub_id, exc)

    async def subscribe(
        self,
        run_id: str,
        replay_history: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to events for run_id.
        Yields event dictionaries as they are published.
        """
        sub_id = str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue()
        current_loop = asyncio.get_running_loop()

        with self._lock:
            if run_id not in self._subscribers:
                self._subscribers[run_id] = {}
            self._subscribers[run_id][sub_id] = queue
            self._subscriber_loops[sub_id] = current_loop

            # Replay existing historical events if requested
            if replay_history and run_id in self._history:
                for past_event in self._history[run_id]:
                    queue.put_nowait(past_event)

        logger.debug("Subscriber %s registered for run_id: %s", sub_id, run_id)

        try:
            while True:
                event = await queue.get()
                yield event
                queue.task_done()

                # 'done' event signals end of run stream
                if event.get("event_type") == "done":
                    break
        finally:
            self.unsubscribe(run_id, sub_id)
            logger.debug("Subscriber %s cleaned up for run_id: %s", sub_id, run_id)

    def unsubscribe(self, run_id: str, subscriber_id: str) -> None:
        """Remove subscriber and free associated resources."""
        with self._lock:
            if run_id in self._subscribers:
                self._subscribers[run_id].pop(subscriber_id, None)
                if not self._subscribers[run_id]:
                    del self._subscribers[run_id]
            self._subscriber_loops.pop(subscriber_id, None)

    def get_subscriber_count(self, run_id: str) -> int:
        """Return count of active subscribers for run_id."""
        with self._lock:
            return len(self._subscribers.get(run_id, {}))

    def get_history(self, run_id: str) -> List[Dict[str, Any]]:
        """Return shallow copy of recorded events for run_id."""
        with self._lock:
            return list(self._history.get(run_id, []))

    def clear(self, run_id: Optional[str] = None) -> None:
        """Clear subscribers and history for run_id, or all runs if None."""
        with self._lock:
            if run_id is not None:
                self._subscribers.pop(run_id, None)
                self._history.pop(run_id, None)
            else:
                self._subscribers.clear()
                self._subscriber_loops.clear()
                self._history.clear()


# ---------------------------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------------------------

_event_bus_instance: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Return the global EventBus singleton."""
    global _event_bus_instance
    with _bus_lock:
        if _event_bus_instance is None:
            _event_bus_instance = EventBus()
        return _event_bus_instance
