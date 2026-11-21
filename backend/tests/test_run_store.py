"""
Unit tests for backend.app.storage.run_store
"""

import uuid
from backend.app.storage.db import init_database
from backend.app.storage.run_store import (
    get_latest_plan,
    get_run,
    get_run_history,
    get_run_steps,
    save_run,
    save_run_step,
    update_plan_approval,
    update_run,
)


def setup_module():
    init_database()


def test_save_and_get_run():
    project_id = str(uuid.uuid4())
    run = save_run(
        project_id=project_id,
        run_type="plan",
        prompt="Build calculator",
        status="queued",
    )
    assert run["id"] is not None
    assert run["project_id"] == project_id
    assert run["run_type"] == "plan"
    assert run["status"] == "queued"
    assert run["prompt"] == "Build calculator"

    fetched = get_run(run["id"])
    assert fetched is not None
    assert fetched["id"] == run["id"]
    assert fetched["status"] == "queued"


def test_update_run():
    project_id = str(uuid.uuid4())
    run = save_run(project_id=project_id, run_type="develop", status="queued")
    run_id = run["id"]

    updated = update_run(
        run_id,
        status="completed",
        plan_text='{"files": []}',
        iteration_count=1,
        tokens_generated=350,
    )
    assert updated is not None
    assert updated["status"] == "completed"
    assert updated["plan_text"] == '{"files": []}'
    assert updated["iteration_count"] == 1
    assert updated["tokens_generated"] == 350


def test_save_and_get_run_steps():
    project_id = str(uuid.uuid4())
    run = save_run(project_id=project_id, run_type="develop")
    run_id = run["id"]

    s1 = save_run_step(run_id, step_index=0, stage="planning", status="started", message="Analyzing")
    s2 = save_run_step(run_id, step_index=1, stage="generating", status="completed", message="Created main.py", duration_ms=450)

    steps = get_run_steps(run_id)
    assert len(steps) == 2
    assert steps[0]["stage"] == "planning"
    assert steps[1]["duration_ms"] == 450

    run_with_steps = get_run(run_id)
    assert len(run_with_steps["steps"]) == 2


def test_get_run_history():
    project_id = str(uuid.uuid4())
    r1 = save_run(project_id=project_id, run_type="plan", prompt="Plan 1")
    r2 = save_run(project_id=project_id, run_type="develop", prompt="Dev 1")

    history = get_run_history(project_id)
    assert len(history) >= 2
    ids = [h["id"] for h in history]
    assert r1["id"] in ids
    assert r2["id"] in ids


def test_get_latest_plan_and_update_plan_approval():
    project_id = str(uuid.uuid4())
    # No plan initially
    assert get_latest_plan(project_id) is None

    # Save run with plan
    plan_content = '{"project_name": "Test", "files": []}'
    save_run(project_id=project_id, run_type="plan", plan_text=plan_content, status="pending_approval")

    latest = get_latest_plan(project_id)
    assert latest is not None
    assert latest["plan_text"] == plan_content

    # Update approval
    approved_content = '{"project_name": "TestApproved", "files": []}'
    update_plan_approval(project_id, approved_content)

    new_latest = get_latest_plan(project_id)
    assert new_latest["status"] == "approved"
    assert "TestApproved" in new_latest["plan_text"]
