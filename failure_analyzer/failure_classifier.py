import re

def clean_terminal_codes(text):
    """Remove ANSI color and formatting codes from text."""
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text or "")


def analyze_failure(error_message, traceback=""):
    """
    Analyze a test failure and return its category,
    likely cause, confidence, evidence, and suggestions.
    """
    error_message = str(error_message or "").strip()
    traceback = str(traceback or "").strip()

    error_text = f"{error_message}\n{traceback}".lower()
    clean_error = clean_terminal_codes(error_message)
    clean_traceback = clean_terminal_codes(traceback)

    combined_text = f"{clean_error}\n{clean_traceback}".lower()

    category = "Unknown Failure"
    cause = "The error does not match a recognized failure pattern."
    confidence = "Low"
    evidence = clean_error or clean_traceback
    suggestions = [
        "Review the complete traceback and application logs.",
        "Reproduce the failure and identify the first relevant error.",
        "Add a specific classification rule when the cause is understood.",
    ]

    # 1. Element lookup and interaction failures
    element_patterns = [
        "nosuchelementexception",
        "no such element",
        "element not found",
        "unable to locate element",
        "elementnotinteractable",
        "element is not interactable",
    ]

    matched_element = next(
        (p for p in element_patterns if p in error_text), None
    )

    # 2. Timeout and synchronization failures
    timeout_patterns = ["timeout", "timed out"]
    matched_timeout = next(
        (p for p in timeout_patterns if p in error_text), None
    )

    # 3. Assertion failures
    assertion_patterns = [
        "assertionerror",
        "assertion failed",
        "assert ",
    ]
    matched_assertion = next(
        (p for p in assertion_patterns if p in error_text), None
    )

    # 4. Connection failures
    connection_patterns = [
        "connection refused",
        "connection reset",
        "connectionerror",
        "connection error",
        "network is unreachable",
        "failed to establish a new connection",
    ]
    matched_connection = next(
        (p for p in connection_patterns if p in error_text), None
    )

    # 5. API and HTTP failures
    api_patterns = [
        "httperror",
        "api error",
        "status code",
        "response status",
        "http 4",
        "http 5",
        "http 429",
        "http 401",
        "http 403",
    ]
    matched_api = next(
        (p for p in api_patterns if p in error_text), None
    )

    # Prioritize specific UI errors before general assertions or API errors.
    if matched_element:
        category = "Element Not Found"
        confidence = "High"
        evidence = matched_element

        if "interactable" in matched_element:
            cause = (
                "The element may exist but cannot currently be interacted "
                "with because it is hidden, disabled, obstructed, or not ready."
            )
            suggestions = [
                "Check whether the element is visible and enabled.",
                "Wait for overlays, animations, or transitions to finish.",
                "Verify that the element is in the expected screen state.",
                "Check whether another element is intercepting the interaction.",
            ]
        else:
            cause = (
                "The automation could not locate the expected UI element. "
                "The locator, screen state, or element availability may "
                "be responsible."
            )
            suggestions = [
                "Verify the locator, resource ID, XPath, or selector.",
                "Confirm that the expected screen or page is displayed.",
                "Check whether the element is visible and enabled.",
                "Wait for the screen to finish loading before locating the element.",
            ]

    elif matched_timeout:
        category = "Timeout"
        confidence = "High"
        evidence = matched_timeout

        if any(term in error_text for term in [
            "element", "locator", "visible", "clickable", "wait"
        ]):
            cause = (
                "An expected UI condition may not have become true "
                "within the configured wait period."
            )
            suggestions = [
                "Verify the element locator and expected UI state.",
                "Use an explicit wait for the required condition.",
                "Check for slow rendering, animation, or delayed response.",
                "Review the timeout value rather than increasing it blindly.",
            ]
        else:
            cause = (
                "The operation did not complete within the configured "
                "time limit."
            )
            suggestions = [
                "Identify which operation timed out from the traceback.",
                "Check application responsiveness and service availability.",
                "Review timeout settings and network or device performance.",
            ]

    elif matched_connection:
        category = "API Failure"
        confidence = "Medium"
        evidence = matched_connection
        cause = (
            "A connection could not be established or maintained. "
            "The service, network, or endpoint may be unavailable."
        )
        suggestions = [
            "Verify that the target service is running.",
            "Check the endpoint, port, and network connection.",
            "Inspect service logs for connection-related errors.",
            "Retry only if the operation is safe to repeat.",
        ]

    elif matched_assertion:
        category = "Assertion Failure"
        confidence = "High"
        evidence = matched_assertion

        # Search both the error message and traceback.
        mismatch_match = re.search(
            r"assert\s+(['\"])(.*?)\1\s*==\s*(['\"])(.*?)\3",
            combined_text,
        )

        if mismatch_match:
            actual_value = mismatch_match.group(2)
            expected_value = mismatch_match.group(4)

            cause = (
                f"The actual value '{actual_value}' did not match "
                f"the expected value '{expected_value}'. Check whether "
                "the test data, expected result, or application behavior "
                "is correct."
            )

            suggestions = [
                f"Investigate why the actual value was '{actual_value}'.",
                f"Verify whether '{expected_value}' is the correct expected value.",
                "Validate the test data and preconditions.",
                "Inspect the application output at failure time.",
                "Use the traceback to locate the failing assertion.",
            ]

            evidence = clean_terminal_codes(mismatch_match.group(0))

        else:
            cause = (
                "The actual result did not match the expected result. "
                "The application behavior, test data, or assertion may "
                "need investigation."
            )

            suggestions = [
                "Compare the expected value with the actual value.",
                "Inspect the response, UI state, or device output at failure time.",
                "Validate the test data and preconditions.",
                "Use the traceback to locate the failing assertion.",
            ]

            evidence = clean_terminal_codes(error_message or combined_text)

    elif matched_api:
        category = "API Failure"
        confidence = "High"
        evidence = matched_api
        if any(code in error_text for code in [
            "http 401", "http 403", "http 404", "http 429",
            "status code 401", "status code 403",
            "status code 404", "status code 429",
        ]):
            cause = (
                "The API returned a client-error response. "
                "The request, authentication, permissions, or "
                "resource availability may need investigation."
            )
            suggestions = [
                "Verify the endpoint URL and HTTP method.",
                "Check authentication credentials and permissions.",
                "Confirm that the requested resource exists.",
                "For HTTP 429, check rate limits and retry guidance.",
                "Inspect the response body for error details.",
            ]

        elif any(code in error_text for code in [
            "http 500", "http 502", "http 503", "http 504",
            "status code 500", "status code 502",
            "status code 503", "status code 504",
        ]):
            cause = (
                "The API returned a server-error response. "
                "The service may be experiencing an internal error, "
                "overload, or an upstream dependency problem."
            )
            suggestions = [
                "Inspect the response body and server logs.",
                "Check service health and upstream dependencies.",
                "Verify whether the issue is reproducible.",
                "Retry only when the operation is safe to repeat.",
            ]

        else:
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

    # Use the actual error text as supporting evidence when available.
    if category != "Unknown Failure" and combined_text:
        evidence = clean_terminal_codes(error_message or combined_text)
        evidence = evidence[:500]

    return {
        "category": category,
        "likely_cause": cause,
        "confidence": confidence,
        "evidence": evidence,
        "suggestions": suggestions,
        "error_message": error_message,
    }


def classify_failure(error_message, traceback=""):
    """Classify a test failure based on its error message and traceback."""
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
        print("Troubleshooting suggestions:")
        for suggestion in analysis["suggestions"]:
            print(f" - {suggestion}")
        print("-" * 50)
