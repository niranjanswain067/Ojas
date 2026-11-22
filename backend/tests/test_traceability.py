"""
Tests for Traceability storage and coverage engine (Phase 19).
"""

import json
import uuid
import pytest
from backend.app.storage.db import init_db, execute_query
from backend.app.storage.project_store import create_project
from backend.app.storage.document_store import create_document
from backend.app.storage.test_store import save_test_case, update_test_case_status
from backend.app.storage.bug_store import save_bug_report
from backend.app.storage.traceability import (
    link_req_to_code,
    link_req_to_test,
    link_test_to_bug,
    link_code_to_bug,
    get_traceability_links,
    auto_sync_traceability,
    get_coverage,
)


from backend.app.storage.run_store import save_run

@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_explicit_traceability_links():
    proj = create_project(f"TraceProj_{uuid.uuid4().hex[:6]}", "Test Project for Traceability")
    p_id = proj["id"]

    # Create run for foreign key
    r = save_run(project_id=p_id, run_type="test")
    r_id = r["id"]

    # Create matching entities for foreign keys
    chunk_id = str(uuid.uuid4())
    execute_query(
        """
        INSERT INTO code_chunks (id, project_id, file_path, symbol_name, symbol_type, content, start_line, end_line, content_hash, created_at, updated_at)
        VALUES (?, ?, 'calc.py', 'add', 'function', 'def add(a, b): return a + b', 1, 5, 'hash1', '2026-11-20T12:00:00', '2026-11-20T12:00:00')
        """,
        (chunk_id, p_id),
    )

    tc = save_test_case(
        project_id=p_id,
        tc_id="TC-001",
        name="test_add",
        file_path="tests/test_calc.py",
        function_name="test_add",
    )
    tc_id = tc["id"]

    bug = save_bug_report(
        project_id=p_id,
        run_id=r_id,
        bug_id="B-001",
        expected_result="Pass",
        actual_result="Fail",
        req_id="REQ-001",
        tc_id="TC-001",
        severity="high",
    )
    bug_id = bug["id"]

    # Explicit linking
    l1 = link_req_to_code(p_id, "REQ-001", code_chunk_id=chunk_id)
    assert l1 is not None

    l2 = link_req_to_test(p_id, "REQ-001", test_case_id=tc_id)
    assert l2 is not None

    l3 = link_test_to_bug(p_id, test_case_id=tc_id, bug_report_id=bug_id)
    assert l3 is not None

    l4 = link_code_to_bug(p_id, code_chunk_id=chunk_id, bug_report_id=bug_id)
    assert l4 is not None

    # Retrieve all links
    all_links = get_traceability_links(p_id)
    assert len(all_links) == 4

    # Filter by link type
    req_code = get_traceability_links(p_id, link_type="req_to_code")
    assert len(req_code) == 1
    assert req_code[0]["req_id"] == "REQ-001"
    assert req_code[0]["code_chunk_id"] == chunk_id

    test_bug = get_traceability_links(p_id, link_type="test_to_bug")
    assert len(test_bug) == 1
    assert test_bug[0]["test_case_id"] == tc_id


def test_coverage_and_auto_sync():
    proj = create_project(f"CoverageProj_{uuid.uuid4().hex[:6]}", "Project for coverage computation")
    p_id = proj["id"]

    # 1. Create document and requirement chunks
    doc = create_document(
        project_id=p_id,
        filename="reqs.md",
        file_type="markdown",
        file_hash="hash1",
        file_path="docs/reqs.md",
    )
    doc_id = doc["id"]

    execute_query(
        """
        INSERT INTO chunks (id, document_id, project_id, chunk_index, chunk_type, content, token_count, req_id, heading, content_hash, created_at)
        VALUES (?, ?, ?, ?, 'requirement', ?, ?, ?, ?, 'chash1', '2026-11-20T12:00:00')
        """,
        (str(uuid.uuid4()), doc_id, p_id, 0, "The system shall add books to inventory.", 10, "REQ-001", "Add Book Functionality"),
    )
    execute_query(
        """
        INSERT INTO chunks (id, document_id, project_id, chunk_index, chunk_type, content, token_count, req_id, heading, content_hash, created_at)
        VALUES (?, ?, ?, ?, 'requirement', ?, ?, ?, ?, 'chash2', '2026-11-20T12:00:00')
        """,
        (str(uuid.uuid4()), doc_id, p_id, 1, "The system shall search books by title.", 10, "REQ-002", "Search Books"),
    )

    # Create run for bug foreign key
    cov_run = save_run(project_id=p_id, run_type="test")
    cov_run_id = cov_run["id"]

    # 2. Add test cases linked to REQ-001
    tc1 = save_test_case(
        project_id=p_id,
        tc_id="TC-001",
        name="test_add_book_valid",
        file_path="tests/test_library.py",
        function_name="test_add_book_valid",
        linked_req_ids=["REQ-001"],
    )
    update_test_case_status(p_id, "TC-001", "passed")

    # Add failing test case linked to REQ-002
    tc2 = save_test_case(
        project_id=p_id,
        tc_id="TC-002",
        name="test_search_empty",
        file_path="tests/test_library.py",
        function_name="test_search_empty",
        linked_req_ids=["REQ-002"],
    )
    update_test_case_status(p_id, "TC-002", "failed")

    # Add a bug report for TC-002
    save_bug_report(
        project_id=p_id,
        run_id=cov_run_id,
        bug_id="B-002",
        tc_id="TC-002",
        req_id="REQ-002",
        severity="medium",
        expected_result="Return empty list",
        actual_result="Raises KeyError",
    )

    # 3. Compute coverage
    coverage = get_coverage(p_id)
    assert len(coverage) >= 2

    cov_dict = {c["req_id"]: c for c in coverage}
    assert "REQ-001" in cov_dict
    assert "REQ-002" in cov_dict

    # REQ-001 should be passing
    assert cov_dict["REQ-001"]["status"] == "passing"
    assert len(cov_dict["REQ-001"]["test_cases"]) == 1
    assert cov_dict["REQ-001"]["test_cases"][0]["tc_id"] == "TC-001"
    assert len(cov_dict["REQ-001"]["bugs"]) == 0

    # REQ-002 should be failing
    assert cov_dict["REQ-002"]["status"] == "failing"
    assert len(cov_dict["REQ-002"]["bugs"]) == 1
    assert cov_dict["REQ-002"]["bugs"][0]["tc_id"] == "TC-002"
