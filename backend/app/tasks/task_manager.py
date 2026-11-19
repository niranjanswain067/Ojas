"""
Ojas Background Task Manager.

Enforces single-task execution (ThreadPoolExecutor with max_workers=1)
and provides cancellation events and status tracking.
"""

import inspect
import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """
    Manages asynchronous background execution of developer and test tasks.

    Constraints:
    - Runs at most one background task at a time.
    - Rejects concurrent task submissions with False (HTTP 409 equivalent).
    - Supports cooperative cancellation via threading.Event.
    """

    def __init__(self, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ojas-task-worker",
        )
        self._lock = threading.RLock()
        self._current_run_id: Optional[str] = None
        self._current_future: Optional[Future] = None
        self._cancel_events: Dict[str, threading.Event] = {}
        self._statuses: Dict[str, TaskStatus] = {}
        self._errors: Dict[str, Optional[str]] = {}
        self._start_times: Dict[str, float] = {}
        self._end_times: Dict[str, float] = {}

    def is_busy(self) -> bool:
        """Return True if a task is currently executing in the background."""
        with self._lock:
            if self._current_run_id is None:
                return False
            status = self._statuses.get(self._current_run_id)
            return status == TaskStatus.RUNNING

    def get_current_run_id(self) -> Optional[str]:
        """Return the run_id of the currently executing task, if any."""
        with self._lock:
            return self._current_run_id if self.is_busy() else None

    def get_status(self, run_id: str) -> Optional[TaskStatus]:
        """Return the TaskStatus of the given run_id, or None if unknown."""
        with self._lock:
            return self._statuses.get(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        """Check if cancellation has been requested for run_id."""
        with self._lock:
            event = self._cancel_events.get(run_id)
            return event.is_set() if event is not None else False

    def get_cancel_event(self, run_id: str) -> Optional[threading.Event]:
        """Return the threading.Event used to signal cancellation for run_id."""
        with self._lock:
            return self._cancel_events.get(run_id)

    def cancel(self, run_id: str) -> bool:
        """
        Request cancellation of the task associated with run_id.
        Sets the threading.Event which the task must check cooperatively.
        Returns True if the task was found and running, False otherwise.
        """
        with self._lock:
            if run_id not in self._cancel_events:
                logger.warning("Attempted to cancel unknown task: %s", run_id)
                return False

            if self._statuses.get(run_id) != TaskStatus.RUNNING:
                logger.info("Task %s is not running (status: %s)", run_id, self._statuses.get(run_id))
                return False

            logger.info("Signalling cancellation for run_id: %s", run_id)
            self._cancel_events[run_id].set()
            return True

    def submit(
        self,
        task_fn: Callable[..., Any],
        run_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Submit a callable to run in the background.

        Returns:
            True if task was accepted and scheduled.
            False if another task is already executing (busy).
        """
        with self._lock:
            if self.is_busy():
                logger.warning(
                    "Rejected task submission for %s: another task (%s) is already running",
                    run_id,
                    self._current_run_id,
                )
                return False

            cancel_event = threading.Event()
            self._cancel_events[run_id] = cancel_event
            self._statuses[run_id] = TaskStatus.RUNNING
            self._errors[run_id] = None
            self._start_times[run_id] = time.time()
            self._current_run_id = run_id

            logger.info("Scheduling task for run_id: %s", run_id)
            future = self._executor.submit(
                self._run_task,
                task_fn,
                run_id,
                cancel_event,
                *args,
                **kwargs,
            )
            self._current_future = future
            return True

    def _run_task(
        self,
        task_fn: Callable[..., Any],
        run_id: str,
        cancel_event: threading.Event,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Wrapper executed inside the thread pool."""
        logger.info("Starting background task for run_id: %s", run_id)
        try:
            # Check if task_fn accepts cancel_event parameter
            sig = inspect.signature(task_fn)
            if "cancel_event" in sig.parameters:
                task_fn(*args, cancel_event=cancel_event, **kwargs)
            elif "run_id" in sig.parameters and "run_id" not in kwargs:
                task_fn(*args, run_id=run_id, **kwargs)
            else:
                task_fn(*args, **kwargs)

            # Determine final status
            with self._lock:
                if cancel_event.is_set():
                    self._statuses[run_id] = TaskStatus.CANCELLED
                    logger.info("Task %s completed as CANCELLED", run_id)
                else:
                    self._statuses[run_id] = TaskStatus.COMPLETED
                    logger.info("Task %s completed successfully", run_id)

        except Exception as exc:
            with self._lock:
                if cancel_event.is_set():
                    self._statuses[run_id] = TaskStatus.CANCELLED
                    logger.info("Task %s aborted via cancellation with exception: %s", run_id, exc)
                else:
                    self._statuses[run_id] = TaskStatus.FAILED
                    self._errors[run_id] = str(exc)
                    logger.exception("Task %s failed with error: %s", run_id, exc)

        finally:
            with self._lock:
                self._end_times[run_id] = time.time()
                if self._current_run_id == run_id:
                    self._current_run_id = None
                    self._current_future = None

    def get_task_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Return diagnostic metrics and info for run_id."""
        with self._lock:
            if run_id not in self._statuses:
                return None
            start = self._start_times.get(run_id, 0.0)
            end = self._end_times.get(run_id)
            duration = (end - start) if end else (time.time() - start if start else 0.0)
            return {
                "run_id": run_id,
                "status": self._statuses[run_id].value,
                "error": self._errors.get(run_id),
                "duration_seconds": round(duration, 3),
                "is_cancelled": self._cancel_events.get(run_id, threading.Event()).is_set(),
            }

    def reset(self) -> None:
        """Reset internal state. Primarily used for unit testing."""
        with self._lock:
            self._current_run_id = None
            self._current_future = None
            self._cancel_events.clear()
            self._statuses.clear()
            self._errors.clear()
            self._start_times.clear()
            self._end_times.clear()


# ---------------------------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------------------------

_task_manager_instance: Optional[TaskManager] = None
_instance_lock = threading.Lock()


def get_task_manager() -> TaskManager:
    """Return the global TaskManager singleton."""
    global _task_manager_instance
    with _instance_lock:
        if _task_manager_instance is None:
            _task_manager_instance = TaskManager()
        return _task_manager_instance
