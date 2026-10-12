
import json

from failure_analyzer.failure_collector import collect_failures


def test_collects_failed_tests(tmp_path):
    report = {
        "tests": [
            {
                "nodeid": "tests/test_login.py::test_invalid_login",
                "outcome": "failed",
                "call": {
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
                "call": {"duration": 0.05},
            },
        ]
    }

    report_file = tmp_path / "test_collects_failed_results.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")

    failures = collect_failures(report_file)

    assert len(failures) == 1
    assert failures[0]["status"] == "failed"
    assert failures[0]["test_name"] == (
        "tests/test_login.py::test_invalid_login"
    )
    assert failures[0]["error"] == "AssertionError"


def test_missing_report_raises_error(tmp_path):
    missing_file = tmp_path / "missing.json"

    try:
        collect_failures(missing_file)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")
