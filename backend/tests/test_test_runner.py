"""
Unit tests for backend.app.validation.test_runner
"""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from backend.app.validation.test_runner import (
    TestCaseResult,
    TestRunResult,
    TestRunner,
)


def test_find_test_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        proj_dir = base / "proj1"
        proj_dir.mkdir()

        (proj_dir / "app.py").write_text("def add(a, b): return a + b")
        (proj_dir / "test_math.py").write_text("def test_add(): pass")
        (proj_dir / "helper_test.py").write_text("def test_help(): pass")

        runner = TestRunner(workspace_base=base)
        files = runner.find_test_files(proj_dir)
        names = {f.name for f in files}
        assert "test_math.py" in names
        assert "helper_test.py" in names
        assert "app.py" not in names


def test_parse_junit_xml():
    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
    <testsuites>
        <testsuite name="pytest" errors="0" failures="1" skipped="1" tests="3" time="0.123">
            <testcase classname="test_service" file="tests/test_service.py" name="test_success" time="0.045"/>
            <testcase classname="test_service" file="tests/test_service.py" name="test_failure" time="0.050">
                <failure message="assert 1 == 2">def test_failure(): assert 1 == 2</failure>
            </testcase>
            <testcase classname="test_service" file="tests/test_service.py" name="test_skip" time="0.001">
                <skipped message="reason: not implemented"/>
            </testcase>
        </testsuite>
    </testsuites>
    """
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w", encoding="utf-8") as f:
        f.write(sample_xml)
        xml_path = Path(f.name)

    try:
        runner = TestRunner()
        results = runner.parse_junit_xml(xml_path)

        assert len(results) == 3
        r_pass = next(r for r in results if r.name == "test_success")
        assert r_pass.result == "passed"
        assert r_pass.duration_ms == 45

        r_fail = next(r for r in results if r.name == "test_failure")
        assert r_fail.result == "failed"
        assert "assert 1 == 2" in (r_fail.error_message or "")

        r_skip = next(r for r in results if r.name == "test_skip")
        assert r_skip.result == "skipped"
    finally:
        if xml_path.exists():
            xml_path.unlink()


def test_run_tests_empty_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = TestRunner(workspace_base=Path(tmpdir))
        res = runner.run_tests("nonexistent_proj")
        assert res.success is False
        assert "does not exist" in res.summary


def test_run_tests_no_test_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        proj_dir = base / "proj_no_tests"
        proj_dir.mkdir()
        runner = TestRunner(workspace_base=base)
        res = runner.run_tests("proj_no_tests")
        assert res.success is True
        assert res.total == 0
        assert "No test files found" in res.summary
