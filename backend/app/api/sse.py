"""
SSE (Server-Sent Events) and Runs progress router.

Endpoints:
    GET  /api/runs/{run_id}/events  - Live SSE progress event stream
    POST /api/runs/{run_id}/cancel  - Request run cancellation
    GET  /api/runs/{run_id}/status  - Get current run status and metrics
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.events.event_bus import get_event_bus
from backend.app.tasks.task_manager import TaskStatus, get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/runs", tags=["runs-events"])


class CancelResponse(BaseModel):
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    run_id: str
    status: str
    is_busy: bool
    error: str | None = None
    duration_seconds: float = 0.0


async def _sse_generator(request: Request, run_id: str) -> AsyncGenerator[str, None]:
    """
    Stream Server-Sent Events from the EventBus to the connected HTTP client.
    Handles client disconnection and timeouts cleanly.
    """
    event_bus = get_event_bus()

    # Initial handshake event to establish active connection
    yield f"event: connected\ndata: {json.dumps({'run_id': run_id, 'status': 'connected'})}\n\n"

    try:
        async for event in event_bus.subscribe(run_id):
            if await request.is_disconnected():
                logger.info("Client disconnected from SSE stream for run_id: %s", run_id)
                break

            event_type = event.get("event_type", "message")
            data = event.get("data", {})

            # Standard SSE format:
            # event: <type>
            # data: <json_string>
            payload = json.dumps(data)
            yield f"event: {event_type}\ndata: {payload}\n\n"

            # 'done' event closes the SSE stream naturally
            if event_type == "done":
                logger.info("Run %s sent 'done' event; terminating SSE stream", run_id)
                break

    except asyncio.CancelledError:
        logger.debug("SSE stream cancelled for run_id: %s", run_id)
    except Exception as exc:
        logger.exception("Unexpected error in SSE stream for run_id %s: %s", run_id, exc)


@router.get(
    "/{run_id}/events",
    summary="Subscribe to run events (SSE)",
    description=(
        "Establishes a Server-Sent Events (SSE) connection that streams real-time "
        "progress updates (stage, file, token, check, test, bug, iteration, done) "
        "for the specified run_id."
    ),
    response_class=StreamingResponse,
)
async def stream_run_events(run_id: str, request: Request) -> StreamingResponse:
    """Stream live events for run_id using text/event-stream."""
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        _sse_generator(request, run_id),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post(
    "/{run_id}/cancel",
    response_model=CancelResponse,
    summary="Cancel active run",
    description="Requests cancellation of an actively executing background task.",
)
async def cancel_run(run_id: str) -> CancelResponse:
    """Request cancellation for the given run_id."""
    tm = get_task_manager()
    success = tm.cancel(run_id)

    if not success:
        # Check current status
        current_status = tm.get_status(run_id)
        if current_status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            return CancelResponse(
                status=current_status.value,
                message=f"Run {run_id} is already finished ({current_status.value}).",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found or not active.",
        )

    # Publish cancellation event to subscribers
    get_event_bus().publish(
        run_id,
        "done",
        {"status": "cancelled", "stop_reason": "user_cancelled", "message": "Run cancellation requested"},
    )

    return CancelResponse(
        status="cancelled",
        message="Run cancellation requested",
    )


@router.get(
    "/{run_id}/status",
    response_model=TaskStatusResponse,
    summary="Get run status",
    description="Query execution status and diagnostics for a background run.",
)
async def get_run_status(run_id: str) -> TaskStatusResponse:
    """Return task execution status and duration metrics."""
    tm = get_task_manager()
    info = tm.get_task_info(run_id)

    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    return TaskStatusResponse(
        run_id=run_id,
        status=info["status"],
        is_busy=tm.is_busy(),
        error=info.get("error"),
        duration_seconds=info.get("duration_seconds", 0.0),
    )

