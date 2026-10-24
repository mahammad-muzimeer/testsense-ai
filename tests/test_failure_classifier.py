
import pytest
from failure_analyzer.failure_classifier import classify_failure


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
