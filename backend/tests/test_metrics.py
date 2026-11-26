"""
Unit tests for backend/app/metrics.py.
"""

from pathlib import Path

from backend.app.metrics import (
    RunMetrics,
    compute_mrr,
    compute_recall_at_k,
    get_process_memory_mb,
    load_all_metrics,
    save_run_metrics,
)


def test_get_process_memory_mb_returns_positive():
    mem = get_process_memory_mb()
    assert isinstance(mem, float)
    assert mem >= 0.0


def test_compute_recall_at_k():
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    relevant = ["doc2", "doc4", "doc6"]
    assert compute_recall_at_k(retrieved, relevant, k=5) == round(2 / 3, 4)
    assert compute_recall_at_k(retrieved, relevant, k=2) == round(1 / 3, 4)
    assert compute_recall_at_k(retrieved, [], k=5) == 0.0


def test_compute_mrr():
    assert compute_mrr(["doc1", "doc2", "doc3"], ["doc2"]) == 0.5
    assert compute_mrr(["doc1", "doc2", "doc3"], ["doc1"]) == 1.0
    assert compute_mrr(["doc1", "doc2", "doc3"], ["doc9"]) == 0.0


def test_run_metrics_lifecycle(tmp_path: Path):
    metrics_file = tmp_path / "metrics.json"
    rm = RunMetrics(run_id="run-1", project_id="proj-1")
    rm.record_stage("planning", 1.25)
    rm.record_stage("generating", 2.5)
    rm.record_generation("planning", tokens_generated=100, duration_seconds=2.0)
    rm.record_generation("generating", tokens_generated=200, duration_seconds=4.0)
    rm.fix_loop_iterations = 2

    assert rm.stage_durations_seconds["planning"] == 1.25
    assert rm.stage_durations_seconds["generating"] == 2.5
    assert rm.total_tokens_generated == 300
    assert rm.avg_tokens_per_second == 50.0
    assert len(rm.generation_calls) == 2

    # Save directly to temp path
    payload = rm.finalize("done")
    save_run_metrics(payload, metrics_path=metrics_file)

    loaded = load_all_metrics(metrics_path=metrics_file)
    assert len(loaded) == 1
    assert loaded[0]["run_id"] == "run-1"
    assert loaded[0]["status"] == "done"
    assert loaded[0]["fix_loop_iterations"] == 2
