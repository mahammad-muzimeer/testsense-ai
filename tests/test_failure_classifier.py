
import pytest
from failure_analyzer.failure_classifier import classify_failure, analyze_failure


@pytest.mark.parametrize(
    "error, expected",
    [
        # Assertion failures
        ("AssertionError: expected 200 but got 500", "Assertion Failure"),
        ("assert 10 == 20", "Assertion Failure"),

        # Timeout failures
        ("Timeout waiting for element", "Timeout"),
        ("TimeoutException: operation timed out", "Timeout"),

        # Element locator failures
        ("NoSuchElementException: unable to locate element", "Element Not Found"),
        ("Element not found on the page", "Element Not Found"),

        # API failures
        ("API Error: status code 500", "API Failure"),
        ("HTTPError: server returned an error", "API Failure"),

        # Unknown failures
        ("Unexpected application crash", "Unknown Failure"),
        ("Some unrelated error occurred", "Unknown Failure"),
    ],
)
def test_classify_failure(error, expected):
    assert classify_failure(error) == expected


def test_empty_error_returns_unknown_failure():
    assert classify_failure("") == "Unknown Failure"


def test_none_error_returns_unknown_failure():
    assert classify_failure(None) == "Unknown Failure"

def test_traceback_can_help_classify_failure():
    error = ""
    traceback = "TimeoutException: waiting for the login button"

    assert classify_failure(error, traceback) == "Timeout"

def test_connection_error_returns_api_failure():
    assert classify_failure("ConnectionError: connection refused") == "API Failure"

def test_http_404_returns_api_failure():
    assert classify_failure("HTTP 404: resource not found") == "API Failure"

def test_http_503_returns_api_failure():
    assert classify_failure("HTTP 503: service unavailable") == "API Failure"

def test_element_not_interactable_returns_element_not_found():
    assert classify_failure(
        "ElementNotInteractable: element is not interactable"
    ) == "Element Not Found"

def test_timeout_in_traceback_returns_timeout():
    error = "Test execution failed"
    traceback = "TimeoutException: timed out waiting for the submit button"

    assert classify_failure(error, traceback) == "Timeout"

def test_whitespace_error_returns_unknown_failure():
    assert classify_failure("   ") == "Unknown Failure"

def test_analysis_returns_all_expected_fields():
    result = analyze_failure("Timeout waiting for login button")

    assert result["category"] == "Timeout"
    assert result["likely_cause"]
    assert result["confidence"] in ["Low", "Medium", "High"]
    assert result["evidence"]
    assert isinstance(result["suggestions"], list)
    assert len(result["suggestions"]) > 0
    assert "error_message" in result


def test_analysis_preserves_actual_error_as_evidence():
    error = "API Error: status code 500"
    result = analyze_failure(error)

    assert result["category"] == "API Failure"
    assert error.lower() in result["evidence"].lower()


def test_element_interaction_failure_has_relevant_suggestions():
    result = analyze_failure(
        "ElementNotInteractableException: element is not interactable"
    )

    assert result["category"] == "Element Not Found"
    assert any(
        "visible" in suggestion.lower()
        or "interact" in suggestion.lower()
        for suggestion in result["suggestions"]
    )

def test_api_timeout_is_classified_as_timeout():
    result = classify_failure(
        "TimeoutError: API request timed out after 10 seconds"
    )

    assert result == "Timeout"


def test_element_wait_timeout_is_classified_as_timeout():
    result = classify_failure(
        "Timeout waiting for login button to become visible"
    )

    assert result == "Timeout"


def test_api_connection_refused_is_classified_as_api_failure():
    result = classify_failure(
        "ConnectionError: connection refused by server"
    )

    assert result == "API Failure"

def test_api_error_with_assertion_text_is_classified_consistently():
    result = classify_failure(
        "API Error: status code 500; AssertionError: expected 200"
    )

    assert result == "Assertion Failure"

def test_http_404_has_client_error_diagnosis():
    result = analyze_failure("HTTP 404: resource not found")

    assert result["category"] == "API Failure"
    assert "client-error" in result["likely_cause"]
    assert any(
        "resource" in suggestion.lower()
        for suggestion in result["suggestions"]
    )


def test_http_503_has_server_error_diagnosis():
    result = analyze_failure("HTTP 503: service unavailable")

    assert result["category"] == "API Failure"
    assert "server-error" in result["likely_cause"]
    assert any(
        "service" in suggestion.lower()
        for suggestion in result["suggestions"]
    )

def test_assertion_failure_identifies_actual_and_expected_values():
    error_message = "AssertionError: assert 'wrong' == 'admin123'"

    result = analyze_failure(error_message)

    assert result["category"] == "Assertion Failure"
    assert "wrong" in result["likely_cause"]
    assert "admin123" in result["likely_cause"]
    assert any("wrong" in suggestion for suggestion in result["suggestions"])
    assert any("admin123" in suggestion for suggestion in result["suggestions"])
