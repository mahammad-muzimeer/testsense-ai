import pytest

def test_valid_login():
    username = "admin"
    password = "admin123"

    assert username == "admin"
    assert password == "admin123"


@pytest.mark.xfail(
    reason="Intentional failure to demonstrate TestSense AI",
    strict=False,
)
def test_invalid_login():
    username = "admin"
    password = "wrong"

    assert password == "admin123"
