import json
from pathlib import Path


def collect_failures(report_path):
    """Extract failed test details from a PyTest JSON report.
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
        if test.get("outcome") == "failed":
            call_details = test.get("call", {})
            error_details = call_details.get("crash", {})

            failure = {
                "test_name": test.get("nodeid", "Unknown test"),
                "status": test.get("outcome"),
                "duration": call_details.get("duration", 0),
                "error": error_details.get("message", "No error message"),
                "traceback": error_details.get("traceback", ""),
            }

            failures.append(failure)

    return failures


if __name__ == "__main__":
    report_path = "reports/test-results.json"
    failures = collect_failures(report_path)

    print(f"\nTotal failed tests: {len(failures)}")

    for failure in failures:
        print("\n" + "=" * 50)
        print(f"Test     : {failure['test_name']}")
        print(f"Status   : {failure['status']}")
        print(f"Duration : {failure['duration']:.2f} seconds")
        print(f"Error    : {failure['error']}")
        print(f"Traceback:\n{failure['traceback']}")
