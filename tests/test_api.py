import sqlite3
import pytest
from fastapi.testclient import TestClient
from failure_analyzer.api import app
from failure_analyzer import api

client = TestClient(app)

def create_test_database(tmp_path):
    """ Create an isolated SQLite database for API tests."""
    db_path = tmp_path / "test_testsense.db"

    connection = sqlite3.connect(db_path)

    connection.execute(
        """
        CREATE TABLE test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            status TEXT,
            duration REAL,
            error TEXT,
            traceback TEXT,
            category TEXT,
            created_at TEXT,
            run_id INTEGER
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO test_results (
            test_name, status, duration, error,
            traceback, category, created_at, run_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "test_login",
                "passed",
                0.25,
                "",
                "",
                "",
                "2026-10-24 10:00:00",
                1,
            ),
            (
                "test_checkout",
                "failed",
                0.50,
                "AssertionError",
                "assert 1 == 2",
                "Assertion Failure",
                "2026-10-24 10:01:00",
                1,
            ),
            (
                "test_search",
                "passed",
                0.15,
                "",
                "",
                "",
                "2026-10-24 10:02:00",
                2,
            ),
        ],
    )

    connection.commit()
    connection.close()

    return db_path

@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """ Redirect the API to a temporary test database. """
    db_path = create_test_database(tmp_path)
    monkeypatch.setattr(api, "DATABASE_PATH", str(db_path))
    return db_path

def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to TestSense API",
        "status": "running",
    }

def test_results_returns_latest_run(isolated_database):
    response = client.get("/results")

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == 2
    assert len(data["results"]) == 1
    assert data["results"][0]["test_name"] == "test_search"

@pytest.mark.parametrize("limit", [0, -1, 101])
def test_results_rejects_invalid_limit(limit):
    response = client.get("/results", params={"limit": limit})

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "limit must be between 1 and 100"
    )

def test_results_accepts_valid_limit(isolated_database):
    response = client.get("/results", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1

def test_analytics_endpoint(monkeypatch):
    expected_statistics = {
        "total_tests": 10,
        "passed": 9,
        "failed": 0,
        "xfailed": 1,
    }

    monkeypatch.setattr(
        api,
        "get_test_statistics",
        lambda: expected_statistics,
    )

    response = client.get("/analytics")

    assert response.status_code == 200
    assert response.json() == expected_statistics

def test_history_endpoint(monkeypatch):
    expected_history = [
        {
            "run_id": 1,
            "total_tests": 2,
            "passed": 1,
            "failed": 1,
            "pass_rate": 50.0,
        }
    ]

    monkeypatch.setattr(
        api,
        "get_test_history",
        lambda limit: expected_history,
    )

    response = client.get("/analytics/history")

    assert response.status_code == 200
    assert response.json() == {"history": expected_history}


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_history_rejects_invalid_limit(limit):
    response = client.get(
        "/analytics/history",
        params={"limit": limit},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "limit must be between 1 and 100"
    )
