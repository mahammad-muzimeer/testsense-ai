import json
from failure_analyzer.database import create_database, save_test_result
from failure_analyzer.failure_classifier import classify_failure
from pathlib import Path


def collect_failures(report_path):
    """
    Extract failed test details from a PyTest JSON report.

    Run this Command to collect all failed tests.
    python -m failure_analyzer.failure_collector
    """

    report_file = Path(report_path)

    if not report_file.exists():
        raise FileNotFoundError(
            f"Report not found: {report_file}"
        )

    with report_file.open("r", encoding="utf-8") as file:
        report = json.load(file)

    failures = []

    for test in report.get("tests", []):
        if test.get("outcome") != "failed":
            continue

        call_details = test.get("call") or {}
        error_details = call_details.get("crash") or {}

        failures.append({
            "test_name": test.get("nodeid", "Unknown test"),
            "status": test.get("outcome"),
            "duration": call_details.get("duration", 0),
            "error": error_details.get("message", "No error message available"),
            "traceback": error_details.get("traceback", ""),
            "category": classify_failure(
                error_details.get("message", ""),
                error_details.get("traceback", "")
            )
        })

    return failures


def main():
    report_path = Path("reports") / "test-results.json"

    create_database()
    failures = collect_failures(report_path)

    print(f"Total failed tests: {len(failures)}")

    for failure in failures:
        print("\n" + "=" * 60)
        print(f"Test     : {failure['test_name']}")
        print(f"Status   : {failure['status']}")
        print(f"Duration : {failure['duration']:.2f} seconds")
        print(f"Error    : {failure['error']}")
        print(f"Traceback:\n{failure['traceback']}")
        print(f"Category : {failure['category']}")

        save_test_result(
            test_name=failure["test_name"],
            status=failure["status"],
            duration=failure["duration"],
            error=failure["error"],
            traceback=failure["traceback"],
            category=failure["category"]
        )


if __name__ == "__main__":
    main()
