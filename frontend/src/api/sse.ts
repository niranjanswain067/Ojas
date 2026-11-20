/**
 * Client-side SSE (Server-Sent Events) subscription helper.
 */

export interface RunEvent<T = any> {
  event_type: string;
  data: T;
  timestamp?: string;
  run_id?: string;
}

export interface SseSubscriberOptions {
  onEvent?: (event: RunEvent) => void;
  onConnected?: () => void;
  onDone?: (data: any) => void;
  onError?: (err: any) => void;
}

/**
 * Subscribe to the live SSE stream for a given run_id.
 * Returns an unsubscribe function.
 */
export function subscribeRunEvents(
  runId: string,
  options: SseSubscriberOptions
): () => void {
  const url = `/api/runs/${encodeURIComponent(runId)}/events`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener("connected", (e) => {
    try {
      const data = JSON.parse(e.data);
      options.onConnected?.();
      options.onEvent?.({ event_type: "connected", data });
    } catch {
      options.onConnected?.();
    }
  });

  const standardEvents = [
    "stage",
    "file",
    "token",
    "check",
    "test",
    "bug",
    "iteration",
    "done",
    "error",
  ];

  standardEvents.forEach((eventType) => {
    eventSource.addEventListener(eventType, (e) => {
      try {
        const data = JSON.parse(e.data);
        const event: RunEvent = { event_type: eventType, data };
        options.onEvent?.(event);

        if (eventType === "done") {
          options.onDone?.(data);
          eventSource.close();
        }
      } catch (err) {
        options.onError?.(err);
      }
    });
  });

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      options.onEvent?.({ event_type: "message", data });
    } catch {
      options.onEvent?.({ event_type: "message", data: e.data });
    }
  };

  eventSource.onerror = (err) => {
    options.onError?.(err);
  };

  return () => {
    eventSource.close();
  };
}

/**
 * Request cancellation of an active run.
 */
export async function cancelRun(runId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`/api/runs/${encodeURIComponent(runId)}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to cancel run: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Get current run status and metrics.
 */
export async function getRunStatus(
  runId: string
): Promise<{ run_id: string; status: string; is_busy: boolean; error?: string; duration_seconds: number }> {
  const res = await fetch(`/api/runs/${encodeURIComponent(runId)}/status`);
  if (!res.ok) {
    throw new Error(`Failed to fetch run status: ${res.statusText}`);
  }
  return res.json();
}

