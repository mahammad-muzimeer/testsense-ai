
import json
import pytest
from failure_analyzer.failure_collector import collect_failures


def write_report(tmp_path, report, filename="report.json"):
    report_file = tmp_path / filename
    report_file.write_text(json.dumps(report), encoding="utf-8")
    return report_file


def test_collects_passed_and_failed_tests(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_login.py::test_invalid_login",
                "outcome": "failed",
                "duration": 0.15,
                "call": {
                    "outcome": "failed",
                    "duration": 0.15,
                    "crash": {
                        "message": "AssertionError",
                        "traceback": "Expected admin123",
                    },
                },
            },
            {
                "nodeid": "tests/test_login.py::test_valid_login",
                "outcome": "passed",
                "duration": 0.05,
                "call": {
                    "outcome": "passed",
                    "duration": 0.05,
                },
            },
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert len(results) == 2

    failed = results[0]
    assert failed["status"] == "failed"
    assert failed["test_name"] == "tests/test_login.py::test_invalid_login"
    assert failed["error"] == "AssertionError"
    assert failed["traceback"] == "Expected admin123"
    assert failed["category"] == "Assertion Failure"
    assert failed["duration"] == 0.15

    passed = results[1]
    assert passed["status"] == "passed"
    assert passed["test_name"] == "tests/test_login.py::test_valid_login"
    assert passed["category"] == ""
    assert passed["duration"] == 0.05


def test_missing_report_raises_error(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Report not found"):
        collect_failures(missing_file)


def test_empty_report_returns_empty_list(tmp_path):
    report = {"tests": []}

    results = collect_failures(write_report(tmp_path, report))

    assert results == []


def test_invalid_json_raises_error(tmp_path):
    report_file = tmp_path / "invalid.json"
    report_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        collect_failures(report_file)


def test_setup_failure_is_classified(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_app.py::test_startup",
                "outcome": "failed",
                "setup": {
                    "outcome": "failed",
                    "crash": {
                        "message": "NoSuchElementException: missing element",
                    },
                    "longrepr": "Setup failed while finding element",
                },
            }
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert results[0]["error"] == (
        "NoSuchElementException: missing element"
    )
    assert results[0]["traceback"] == "Setup failed while finding element"
    assert results[0]["category"] == "Element Not Found"


def test_expected_failure_is_classified(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_login.py::test_known_issue",
                "outcome": "xfailed",
                "call": {
                    "outcome": "failed",
                    "crash": {
                        "message": "Timeout waiting for element",
                    },
                    "longrepr": "Timed out waiting for the element",
                },
            }
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert len(results) == 1
    assert results[0]["status"] == "xfailed"
    assert results[0]["category"] == "Timeout"


def test_traceback_list_is_converted_to_string(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_app.py::test_error",
                "outcome": "failed",
                "call": {
                    "outcome": "failed",
                    "crash": {
                        "message": "AssertionError",
                    },
                    "longrepr": ["Line 1", "Line 2", "Line 3"],
                },
            }
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert results[0]["traceback"] == "Line 1\nLine 2\nLine 3"
    assert isinstance(results[0]["traceback"], str)


def test_duration_falls_back_to_call_phase(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_app.py::test_duration",
                "outcome": "passed",
                "call": {
                    "outcome": "passed",
                    "duration": 0.234,
                },
            }
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert results[0]["duration"] == 0.234


def test_missing_optional_fields_use_defaults(tmp_path):
    report = {
        "tests": [
            {
                "outcome": "passed",
            }
        ]
    }

    results = collect_failures(write_report(tmp_path, report))

    assert len(results) == 1
    assert results[0]["test_name"] == "Unknown test"
    assert results[0]["status"] == "passed"
    assert results[0]["duration"] == 0
    assert results[0]["error"] == ""
    assert results[0]["traceback"] == ""
    assert results[0]["category"] == ""
