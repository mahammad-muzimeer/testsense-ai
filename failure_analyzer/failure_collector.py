import json
from failure_analyzer.database import (
    create_database, create_test_run, save_test_result,
)
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

    results = []

    for test in report.get("tests", []):
        outcome = test.get("outcome", "unknown")
        call_details = test.get("call") or {}
        setup_details = test.get("setup") or {}
        teardown_details = test.get("teardown") or {}

        failed_phase = next(
            (
                phase
                for phase in (call_details, setup_details, teardown_details)
                if phase.get("outcome") == "failed"
            ),
            call_details,
        )

        error_details = failed_phase.get("crash") or {}
        error = error_details.get("message", "")

        traceback = failed_phase.get("longrepr", "")

        if not traceback:
            traceback = error_details.get("traceback", "")

        # SQLite requires traceback to be a string.
        if isinstance(traceback, list):
            traceback = "\n".join(str(line) for line in traceback)
        elif isinstance(traceback, dict):
            traceback = json.dumps(traceback, indent=2)
        elif traceback is None:
            traceback = ""
        else:
            traceback = str(traceback)

        if not error and traceback:
            error = traceback

        # Ensure the error message is also a string.
        if error is None:
            error = ""
        elif not isinstance(error, str):
            error = str(error)

        category = (
            classify_failure(error, traceback)
            if outcome in ("failed", "xfailed")
            else ""
        )

        results.append({
            "test_name": test.get("nodeid", "Unknown test"),
            "status": outcome,
            "duration": (
                test.get("duration")
                or (test.get("call") or {}).get("duration")
                or 0
            ),
            "error": error,
            "traceback": traceback,
            "category": category
        })

    return results


def main():
    report_path = Path("reports") / "test-results.json"

    create_database()
    results = collect_failures(report_path)

    if not results:
        print("No test results found in the report.")
        return

    run_id = create_test_run()

    for result in results:
        save_test_result(
            test_name=result["test_name"],
            status=result["status"],
            duration=result["duration"],
            error=result["error"],
            traceback=result["traceback"],
            category=result["category"],
            run_id=run_id,
        )

    passed = sum(r["status"] == "passed" for r in results)
    failed = sum(r["status"] == "failed" for r in results)

    print(f"\nTotal tests processed: {len(results)}")
    print(f"Passed tests: {passed}")
    print(f"Failed tests: {failed}")


if __name__ == "__main__":
    main()
