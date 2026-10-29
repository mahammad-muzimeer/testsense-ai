from failure_analyzer.failure_classifier import analyze_failure


scenarios = {
    "Assertion Failure": (
        "AssertionError: assert 'wrong' == 'admin123'"
    ),
    "Timeout": (
        "TimeoutException: Message: "
        "Waiting for element timed out after 10 seconds"
    ),
    "Element Not Found": (
        "NoSuchElementException: Unable to locate element: "
        "#login-button"
    ),
    "API Connection Failure": (
        "ConnectionError: Failed to establish a new connection"
    ),
    "API Status Failure": (
        "HTTPError: 500 Internal Server Error"
    ),
    "Unknown Failure": (
        "UnexpectedWidgetError: Widget state is corrupted"
    ),
}


for scenario, error_message in scenarios.items():
    result = analyze_failure(error_message)

    print("\n" + "=" * 60)
    print(f"Scenario: {scenario}")
    print(f"Detected category: {result['category']}")
    print(f"Likely cause: {result['likely_cause']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Evidence: {result['evidence']}")
    print("Suggestions:")

    for suggestion in result["suggestions"]:
        print(f"  - {suggestion}")