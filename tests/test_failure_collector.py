
import json

from failure_analyzer.failure_collector import collect_failures


def test_collects_failed_tests(tmp_path):
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
                    "duration": 0.05
                },
            },
        ]
    }

    report_file = tmp_path / "test_collects_failed_results.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")

    results = collect_failures(report_file)

    # The collector now returns both failed and passed tests.
    assert len(results) == 2

    assert results[0]["status"] == "failed"
    assert results[0]["test_name"] == (
        "tests/test_login.py::test_invalid_login"
    )
    assert results[0]["error"] == "AssertionError"
    assert results[0]["category"] == "Assertion Failure"

    assert results[1]["status"] == "passed"
    assert results[1]["test_name"] == (
        "tests/test_login.py::test_valid_login"
    )
    assert results[1]["category"] == ""


def test_missing_report_raises_error(tmp_path):
    missing_file = tmp_path / "missing.json"

    try:
        collect_failures(missing_file)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")
