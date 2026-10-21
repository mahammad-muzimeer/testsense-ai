def analyze_failure(error_message, traceback=""):
    """
    Analyze a test failure and return its category,
    likely cause, and suggested troubleshooting steps.
    """
    error_text = f"{error_message} {traceback}".lower()

    if "timeout" in error_text or "timed out" in error_text:
        category = "Timeout"
        cause = (
            "The operation did not complete within the configured"
            "time limit."
        )
        suggestions = [
            "Check whether the application or page is responsive.",
            "Verify the wait condition and timeout configuration.",
            "Check device or network performance if relevant."
        ]

    elif any(term in error_text for term in [
        "no such element",
        "nosuchelementexception",
        "element not found",
        "unable to locate element",
    ]):
        category = "Element Not Found"
        cause = (
            "The automation could not locate the expected "
            "UI element."
        )
        suggestions = [
            "Verify the locator and resource ID.",
            "Check whether the element is visible and enabled.",
            "Wait for the screen or page to finish loading.",
        ]

    elif any(term in error_text for term in [
        "assertionerror",
        "assert ",
        "assertion failed",
    ]):
        category = "Assertion Failure"
        cause = (
            "The actual result did not match the expected result."
        )
        suggestions = [
            "Compare the expected value with the actual value.",
            "Check the test data and application state.",
            "Inspect the tracback to locate the failing assertion."
        ]

    elif any(term in error_text for term in [
        "connectionerror",
        "httperror",
        "status code",
        "api error",
    ]):
        category = "API Failure"
        cause = (
            "The API request may have failed, returned an unexpected status, "
            "or encountered a connection issue."
        )
        suggestions = [
            "Verify the endpoint URL and HTTP method.",
            "Check the response status code and response body.",
            "Verify service availability, authentication, and request data.",
        ]

    else:
        category = "Unknown Failure"
        cause = (
            "The error does not match a recognized failure pattern."
        )
        suggestions = [
            "Review the complete tracback and application logs.",
            "Reproduce the failure and identify the first relevant error.",
            "Add a specific classification rule once the cause is known.",
        ]
    return {
        "category": category,
        "likely_cause": cause,
        "suggestions": suggestions,
        "error_message": error_message,
    }


def classify_failure(error_message, traceback=""):
    """
    Classify a test failure based on its error message and traceback.
    """
    return analyze_failure(error_message, traceback)["category"]


if __name__ == "__main__":
    examples = [
        "AssertionError: expected 200 but got 500",
        "Timeout waiting for element",
        "NoSuchElementException: unable to locate element",
        "API Error: status code 500",
        "Unexpected application crash",
    ]

    for error in examples:
        analysis = analyze_failure(error)
        print(f"\nError: {error}")
        print(f"Category: {analysis['category']}")
        print(f"Likely cause: {analysis['likely_cause']}")
        print("Suggestions actions:")
        for suggestion in analysis["suggestions"]:
            print(f" - {suggestion}")
        print("-" * 50)
