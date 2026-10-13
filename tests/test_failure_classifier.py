import pytest
from failure_analyzer.failure_classifier import classify_failure


@pytest.mark.parametrize(
    "error, expected",
    [
        ("AssertionError: expected 200 but got 500", "Assertion Failure"),
        ("Timeout waiting for element", "Timeout"),
        ("NoSuchElementException: unable to locate element", "Element Not Found"),
        ("API Error: status code 500", "API Failure"),
        ("Unexpected application crash", "Unknown Failure"),
    ],
)
def test_classify_failure(error, expected):
    assert classify_failure(error) == expected
