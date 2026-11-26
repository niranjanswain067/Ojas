"""
Performance Metrics Recorder for Ojas.

Records and persists execution metrics to `logs/metrics.json`:
- Tokens per second (per generation call and average)
- Time per stage (indexing, planning, generating, checking, testing, fixing)
- Peak RAM usage (via Windows Win32 API or /proc fallback, no external deps required)
- Fix loop iterations per run/project
- Retrieval metrics (Recall@k and MRR when ground truth is provided)
"""

import ctypes
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METRICS_FILE = _PROJECT_ROOT / "logs" / "metrics.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def get_process_memory_mb() -> float:
    """
    Return current process RSS / WorkingSet memory in megabytes.
    Uses psutil if available, otherwise Windows kernel32/psapi via ctypes,
    or resource.getrusage on POSIX.
    """
    try:
        import psutil  # type: ignore[import]

        return round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2)
    except Exception:
        pass

    if os.name == "nt":
        try:
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            get_current_process = ctypes.windll.kernel32.GetCurrentProcess
            get_current_process.restype = wintypes.HANDLE

            get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_process_memory_info.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                wintypes.DWORD,
            ]
            get_process_memory_info.restype = wintypes.BOOL

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = get_current_process()
            if get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
                return round(counters.WorkingSetSize / (1024 * 1024), 2)
        except Exception:
            pass
    else:
        try:
            import resource  # type: ignore[import]

            usage = resource.getrusage(resource.RUSAGE_SELF)
            return round(usage.ru_maxrss / 1024.0, 2)
        except Exception:
            pass

    return 0.0


def compute_recall_at_k(
    retrieved_ids: List[str], relevant_ids: List[str], k: int = 5
) -> float:
    """Compute Recall@k for retrieval evaluation."""
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    rel_set = set(relevant_ids)
    return round(len(top_k & rel_set) / len(rel_set), 4)


def compute_mrr(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
    """Compute Mean Reciprocal Rank (MRR) for a single query."""
    if not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids)
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in rel_set:
            return round(1.0 / rank, 4)
    return 0.0


@dataclass
class GenerationMetric:
    """Metrics for a single LLM generation call."""

    stage: str
    tokens_generated: int
    duration_seconds: float
    tokens_per_second: float


@dataclass
class RunMetrics:
    """Aggregated performance metrics for a single orchestrator run."""

    run_id: str
    project_id: str
    started_at: str = field(default_factory=_now_iso)
    completed_at: Optional[str] = None
    status: str = "running"
    stage_durations_seconds: Dict[str, float] = field(default_factory=dict)
    generation_calls: List[GenerationMetric] = field(default_factory=list)
    avg_tokens_per_second: float = 0.0
    total_tokens_generated: int = 0
    peak_ram_mb: float = 0.0
    fix_loop_iterations: int = 0
    retrieval_recall_at_k: Optional[float] = None
    retrieval_mrr: Optional[float] = None

    def record_stage(self, stage_name: str, duration_seconds: float) -> None:
        """Record elapsed time for a pipeline stage and update peak RAM."""
        prev = self.stage_durations_seconds.get(stage_name, 0.0)
        self.stage_durations_seconds[stage_name] = round(prev + max(0.0, duration_seconds), 4)
        self.update_peak_ram()

    def record_generation(
        self, stage: str, tokens_generated: int, duration_seconds: float
    ) -> None:
        """Record token throughput for an LLM generation call."""
        dur = max(duration_seconds, 1e-6)
        tps = round(tokens_generated / dur, 2) if tokens_generated > 0 else 0.0
        self.generation_calls.append(
            GenerationMetric(
                stage=stage,
                tokens_generated=tokens_generated,
                duration_seconds=round(duration_seconds, 4),
                tokens_per_second=tps,
            )
        )
        self.total_tokens_generated = sum(c.tokens_generated for c in self.generation_calls)
        total_gen_time = sum(c.duration_seconds for c in self.generation_calls)
        if total_gen_time > 0:
            self.avg_tokens_per_second = round(
                self.total_tokens_generated / total_gen_time, 2
            )
        self.update_peak_ram()

    def update_peak_ram(self) -> float:
        """Sample process memory and keep the maximum observed value."""
        current = get_process_memory_mb()
        if current > self.peak_ram_mb:
            self.peak_ram_mb = current
        return self.peak_ram_mb

    def finalize(self, status: str) -> Dict[str, Any]:
        """Finalize metrics timestamp, status, and RAM, and persist to logs/metrics.json."""
        self.completed_at = _now_iso()
        self.status = status
        self.update_peak_ram()
        payload = asdict(self)
        save_run_metrics(payload)
        return payload


def save_run_metrics(
    metrics_payload: Dict[str, Any], metrics_path: Path = METRICS_FILE
) -> None:
    """Append or update a run's metrics entry in `logs/metrics.json`."""
    try:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        existing: List[Dict[str, Any]] = []
        if metrics_path.exists():
            try:
                raw = json.loads(metrics_path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    existing = raw
            except Exception:
                existing = []

        run_id = metrics_payload.get("run_id")
        updated = False
        for i, item in enumerate(existing):
            if isinstance(item, dict) and item.get("run_id") == run_id:
                existing[i] = metrics_payload
                updated = True
                break
        if not updated:
            existing.append(metrics_payload)

        metrics_path.write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.warning("Failed to persist run metrics to %s: %s", metrics_path, e)


def load_all_metrics(metrics_path: Path = METRICS_FILE) -> List[Dict[str, Any]]:
    """Read all persisted run metrics from `logs/metrics.json`."""
    if not metrics_path.exists():
        return []
    try:
        raw = json.loads(metrics_path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except Exception as e:
        logger.warning("Failed to read metrics from %s: %s", metrics_path, e)
        return []
