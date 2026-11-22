"""
Tests for ReportWriter and Reports API endpoints (Phase 19).
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage.db import init_db
from backend.app.storage.project_store import create_project
from backend.app.storage.report_writer import ReportWriter
from backend.app.storage.test_store import save_test_case, update_test_case_status
from backend.app.storage.bug_store import save_bug_report

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_report_writer_generation(tmp_path):
    proj = create_project(f"ReportGen_{uuid.uuid4().hex[:6]}", "Testing Report Writer")
    p_id = proj["id"]

    writer = ReportWriter(p_id, base_reports_dir=tmp_path)

    # 1. Dev plan report
    plan_md = writer.generate_development_plan_report("## Step 1: Implement Core Logic")
    assert "Development Plan Report" in plan_md
    assert "Implement Core Logic" in plan_md

    # 2. Bug report
    bugs = [
        {
            "bug_id": "B-001",
            "title": "Division by zero",
            "severity": "critical",
            "status": "open",
            "tc_id": "TC-005",
            "req_id": "REQ-003",
        }
    ]
    bug_md = writer.generate_bug_report(bugs)
    assert "Bug Reports Summary" in bug_md
    assert "B-001" in bug_md
    assert "Division by zero" in bug_md

    # 3. Test report
    tests = [
        {"tc_id": "TC-001", "name": "test_addition", "status": "passed", "duration_ms": 12},
        {"tc_id": "TC-002", "name": "test_subtraction", "status": "failed", "duration_ms": 8},
    ]
    test_md = writer.generate_test_report(tests)
    assert "Test Execution Report" in test_md
    assert "TC-001" in test_md
    assert "TC-002" in test_md

    # 4. Consolidated report
    cons_md = writer.generate_consolidated_report()
    assert "Consolidated Quality & Traceability Report" in cons_md
    assert "Executive Summary" in cons_md
    assert "Requirement Traceability Matrix" in cons_md

    # 5. List reports
    report_list = writer.list_reports()
    assert len(report_list) >= 3


from backend.app.storage.run_store import save_run

def test_reports_api_endpoints():
    proj = create_project(f"ApiReport_{uuid.uuid4().hex[:6]}", "Testing API reports")
    p_id = proj["id"]

    # Create run for foreign key
    r = save_run(project_id=p_id, run_type="test")
    r_id = r["id"]

    # Setup some test data
    save_test_case(
        project_id=p_id,
        tc_id="TC-101",
        name="test_math",
        file_path="tests/test_math.py",
        function_name="test_math",
        linked_req_ids=["REQ-101"],
    )
    update_test_case_status(p_id, "TC-101", "passed")

    save_bug_report(
        project_id=p_id,
        run_id=r_id,
        bug_id="B-102",
        tc_id="TC-102",
        req_id="REQ-102",
        severity="high",
        expected_result="1",
        actual_result="0",
    )

    # 1. Trigger report generation
    gen_resp = client.post(f"/api/projects/{p_id}/reports/generate")
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "report_name" in gen_data
    assert "summary" in gen_data

    # 2. List reports
    list_resp = client.get(f"/api/projects/{p_id}/reports")
    assert list_resp.status_code == 200
    reports = list_resp.json()["reports"]
    assert len(reports) > 0
    assert any("consolidated" in r["name"] for r in reports)

    # 3. Download report in markdown format
    md_resp = client.get(f"/api/projects/{p_id}/reports/consolidated_test_report?format=markdown")
    assert md_resp.status_code == 200
    assert "text/markdown" in md_resp.headers["content-type"]
    assert "Consolidated Quality & Traceability Report" in md_resp.text

    # 4. Download report in json format
    json_resp = client.get(f"/api/projects/{p_id}/reports/consolidated_test_report?format=json")
    assert json_resp.status_code == 200
    j_data = json_resp.json()
    assert j_data["report_name"] == "consolidated_test_report"
    assert "summary" in j_data
    assert "coverage" in j_data

    # 5. Get traceability
    trace_resp = client.get(f"/api/projects/{p_id}/traceability")
    assert trace_resp.status_code == 200
    t_data = trace_resp.json()
    assert t_data["project_id"] == p_id
    assert "coverage" in t_data
