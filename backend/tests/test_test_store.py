"""
Unit tests for backend.app.storage.test_store
"""

import uuid
from backend.app.storage.db import init_database
from backend.app.storage.test_store import (
    extract_test_cases_from_code,
    get_next_tc_id,
    get_test_case_by_tc_id,
    get_test_cases,
    get_test_results,
    register_test_file,
    save_test_case,
    save_test_result,
    update_test_case_status,
)


def setup_module():
    init_database()


def test_extract_test_cases_from_code():
    code = """
# Test file
def test_addition():
    \"\"\"Test addition behavior. REQ-001\"\"\"
    assert 1 + 1 == 2

class TestCalculator:
    def test_subtraction(self):
        \"\"\"Verify subtraction according to REQ-002.\"\"\"
        assert 3 - 1 == 2

    def helper(self):
        pass
"""
    items = extract_test_cases_from_code(code, "tests/test_calc.py")
    assert len(items) == 2

    func_names = [i["function_name"] for i in items]
    assert "test_addition" in func_names
    assert "TestCalculator.test_subtraction" in func_names

    addition = next(i for i in items if i["function_name"] == "test_addition")
    assert "REQ-001" in addition["linked_req_ids"]

    subtraction = next(i for i in items if i["function_name"] == "TestCalculator.test_subtraction")
    assert "REQ-002" in subtraction["linked_req_ids"]


def test_save_and_get_test_case():
    project_id = str(uuid.uuid4())
    tc_id = get_next_tc_id(project_id)
    assert tc_id == "TC-001"

    rec = save_test_case(
        project_id=project_id,
        tc_id=tc_id,
        name="Test Auth Login",
        file_path="tests/test_auth.py",
        function_name="test_login",
        linked_req_ids=["REQ-005"],
        source="user",
        status="not_run",
    )
    assert rec["id"] is not None
    assert rec["tc_id"] == "TC-001"
    assert rec["linked_req_ids"] == ["REQ-005"]

    fetched = get_test_case_by_tc_id(project_id, "TC-001")
    assert fetched is not None
    assert fetched["name"] == "Test Auth Login"

    tc_id2 = get_next_tc_id(project_id)
    assert tc_id2 == "TC-002"


def test_register_test_file():
    project_id = str(uuid.uuid4())
    code = """
def test_alpha():
    \"\"\"Test alpha [REQ-010]\"\"\"
    assert True

def test_beta():
    \"\"\"Test beta [REQ-011]\"\"\"
    assert True
"""
    records = register_test_file(project_id, "tests/test_ab.py", code)
    assert len(records) == 2
    assert records[0]["tc_id"] == "TC-001"
    assert records[1]["tc_id"] == "TC-002"

    all_tcs = get_test_cases(project_id)
    assert len(all_tcs) == 2


def test_save_and_get_test_results():
    project_id = str(uuid.uuid4())
    tc = save_test_case(
        project_id=project_id,
        tc_id="TC-001",
        name="Test One",
        file_path="test_one.py",
    )

    run_id = str(uuid.uuid4())
    r1 = save_test_result(
        run_id=run_id,
        test_case_id=tc["id"],
        tc_id="TC-001",
        result="passed",
        duration_ms=120,
    )
    assert r1["id"] is not None
    assert r1["result"] == "passed"

    results = get_test_results(run_id)
    assert len(results) == 1
    assert results[0]["duration_ms"] == 120
