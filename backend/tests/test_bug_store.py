"""
Unit tests for backend.app.storage.bug_store
"""

import uuid
from backend.app.storage.bug_store import (
    get_bug_report,
    get_bug_reports,
    get_next_bug_id,
    save_bug_report,
    update_bug_report_status,
)
from backend.app.storage.db import init_database


def setup_module():
    init_database()


def test_get_next_bug_id():
    project_id = str(uuid.uuid4())
    bid1 = get_next_bug_id(project_id)
    assert bid1 == "B-001"


def test_save_and_get_bug_report():
    project_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    bug_id = get_next_bug_id(project_id)

    report = save_bug_report(
        project_id=project_id,
        run_id=run_id,
        bug_id=bug_id,
        expected_result="Return 42",
        actual_result="Got None",
        req_id="REQ-001",
        tc_id="TC-001",
        file_path="calculator.py",
        function_name="calculate",
        severity="high",
        probable_cause="Missing return statement in calculate function",
        iteration=1,
    )
    assert report["id"] is not None
    assert report["bug_id"] == "B-001"
    assert report["severity"] == "high"

    fetched = get_bug_report(report["id"])
    assert fetched is not None
    assert fetched["bug_id"] == "B-001"
    assert fetched["function_name"] == "calculate"

    # Next bug id should increment
    bid2 = get_next_bug_id(project_id)
    assert bid2 == "B-002"


def test_update_bug_report_status():
    project_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    bug = save_bug_report(
        project_id=project_id,
        run_id=run_id,
        bug_id="B-001",
        expected_result="200 OK",
        actual_result="500 Internal Error",
    )
    assert bug["status"] == "open"

    update_bug_report_status(bug["id"], status="fixed", fix_description="Handled null pointer")
    updated = get_bug_report(bug["id"])
    assert updated["status"] == "fixed"
    assert updated["fix_description"] == "Handled null pointer"


def test_get_bug_reports_filtered():
    project_id = str(uuid.uuid4())
    run1 = str(uuid.uuid4())
    run2 = str(uuid.uuid4())

    save_bug_report(project_id=project_id, run_id=run1, bug_id="B-001", expected_result="a", actual_result="b", status="open")
    save_bug_report(project_id=project_id, run_id=run2, bug_id="B-002", expected_result="c", actual_result="d", status="fixed")

    all_bugs = get_bug_reports(project_id)
    assert len(all_bugs) == 2

    run1_bugs = get_bug_reports(project_id, run_id=run1)
    assert len(run1_bugs) == 1
    assert run1_bugs[0]["bug_id"] == "B-001"

    open_bugs = get_bug_reports(project_id, status="open")
    assert len(open_bugs) == 1
    assert open_bugs[0]["bug_id"] == "B-001"
