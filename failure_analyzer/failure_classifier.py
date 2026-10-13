
def classify_failure(error_message, traceback=""):
    """
    Classify a test failure based on its error message and traceback.
    """
    error_text = f"{error_message} {traceback}".lower()

    if "timeout" in error_text or "timed out" in error_text:
        return "Timeout"

    if (
        "no such element" in error_text
        or "nosuchelementexception" in error_text
        or "element not found" in error_text
        or "unable to locate element" in error_text
    ):
        return "Element Not Found"

    if (
        "assertionerror" in error_text
        or "assert " in error_text
        or "assertion failed" in error_text
    ):
        return "Assertion Failure"

    if (
        "connectionerror" in error_text
        or "httperror" in error_text
        or "status code" in error_text
        or "api error" in error_text
    ):
        return "API Failure"

    return "Unknown Failure"


if __name__ == "__main__":
    examples = [
        ("AssertionError: expected 200 but got 500", ""),
        ("Timeout waiting for element", ""),
        ("NoSuchElementException: unable to locate element", ""),
        ("API Error: status code 500", ""),
        ("Unexpected application crash", ""),
    ]

    for error, traceback in examples:
        category = classify_failure(error, traceback)
        print(f"Error: {error}")
        print(f"Category: {category}")
        print("-" * 50)
