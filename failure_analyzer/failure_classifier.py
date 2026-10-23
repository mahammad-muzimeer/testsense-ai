def analyze_failure(error_message, traceback=""):
    """
    Analyze a test failure and return its category,
    likely cause, and suggested troubleshooting steps.
    """
    error_message = str(error_message or "")
    traceback = str(traceback or "")
    error_text = f"{error_message}\n{traceback}".lower()

    # Defaults for unrecognized failures.
    category = "Unknown Failure"
    cause = "The error does not match a recognized failure pattern."
    confidence = "Low"
    evidence = "No recognized error pattern found."
    suggestions = [
        "Review the complete tracback and application logs.",
        "Reproduce the failure and identify the first relevant error.",
        "Add a specific classification rul when the cause is understood.",
    ]

    # 1. API and HTTP errors
    api_patterns = [
        "connectionerror",
        "httperror",
        "api error",
        "status code",
        "response status",
        "http 4",
        "http 5",
    ]

    if any(pattern in error_text for pattern in api_patterns):
        category = "API Failure"
        confidence = "High"
        evidence = next(
            pattern for pattern in api_patterns
            if pattern in error_text
        )
        cause = (
            "The API request may have failed because of an unexpected "
            "HTTP response, connectivity issue, or service problem."
        )
        suggestions = [
            "Verify the endpoint URL, HTTP method, and request payload.",
            "Check the response status code and response body.",
            "Verify authentication, service availability, and network connectivity.",
            "Compare the actual response with the API contract.",
        ]

    # 2. Element lookup failures
    elif any(pattern in error_text for pattern in [
        "no such element",
        "nosuchelementexception",
        "element not found",
        "unable to locate element",
    ]):
        category = "Element Not Found"
        confidence = "High"
        evidence = next(
            pattern for pattern in [
                "no such element",
                "nosuchelementexception",
                "element not found",
                "unable to locate element",
            ]
            if pattern in error_text
        )
        if any(term in error_text for term in [
            "resource-id",
            "resource id",
            "locator",
            "xpath",
            "selector",
        ]):
            cause = (
                "The locator may not match the current UI structure, "
                "or the expected element may not be present."
            )
        else:
            cause = (
                "The automation could not locate the expected UI element. "
                "The locator, screen state, or element availability may be "
                "responsible."
            )

        suggestions = [
            "Verify the locator, resource ID, XPath, or selector.",
            "Confirm that the expected screen or page is displayed."
            "Check whether the element is visible and enabled.",
            "Wait for the screen to finish loading before locating the element.",
        ]

    # 3. Timeout and synchronization failures
    elif "timeout" in error_text or "timed out" in error_text:
        category = "Timeout"
        confidence = "High"
        evidence = (
            "timed out" if "timed out" in error_text else "timeout"
        )

        if any(term in error_text for term in [
            "element",
            "locator",
            "visible",
            "clickable",
            "wait",
        ]):
            cause = (
                "An expected UI condition may not have become true "
                "within the configured wait period."
            )
            suggestions = [
                "Verify the element locator and expected UI state.",
                "Use an explicit wait for the required condition.",
                "Check for slow rendering, animation, or delayed response."
                "Review the timeout value without simple increasing it blindly.",
            ]
        else:
            cause = (
                "The operation did not complete within the configured"
                "time limit."
            )
            suggestions = [
                "Identify which operation timed out from the traceback.",
                "Check application responsiveness and service availability.",
                "Review timeout settings and network or device performance.",
            ]

    # 4. Assertion failures
    elif any(term in error_text for term in [
        "assertionerror",
        "assert ",
        "assertion failed",
    ]):
        category = "Assertion Failure"
        confidence = "High"
        evidence = next(
            pattern for pattern in [
                "assertionerror",
                "assertion failed",
                "assert",
            ]
            if pattern in error_text
        )
        cause = (
            "The actual result did not match the expected result. "
            "The application behavior, test data, or assertion may "
            "need investigation."
        )
        suggestions = [
            "Compare the expected value with the actual value.",
            "Inspect the response, UI state, or device output at failure time.",
            "Validate the test data and preconditions.",
            "Use the tracback to locate the failing assertion.",
        ]

    # 5. Other connection errors
    elif any(term in error_text for term in [
        "connection refused",
        "connection reset",
        "connectionerror",
        "network is unreachable",
    ]):
        category = "API Failure"
        confidence = "Medium"
        evidence = next(
            pattern for pattern in [
                "connection refused",
                "connection reset",
                "connectionerror",
                "network is unreachable",
            ]
            if pattern in error_text
        )
        cause = (
            "A connection could not be established or maintained. "
            "The service, network, or endpoint may be unavailable."
        )
        suggestions = [
            "Verify that the target service is running.",
            "Check the endpoint, port, and network connection.",
            "Inspect service logs for connection-related errors.",
        ]

    return {
        "category": category,
        "likely_cause": cause,
        "confidence": confidence,
        "evidence": evidence,
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
        print(f"Confidence: {analysis['confidence']}")
        print(f"Evidence: {analysis['evidence']}")
        print(f"Likely cause: {analysis['likely_cause']}")
        print("Suggestions actions:")
        for suggestion in analysis["suggestions"]:
            print(f" - {suggestion}")
        print("-" * 50)
