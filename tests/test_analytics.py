import sqlite3
import pytest
from failure_analyzer import analytics


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create an isolated database for analytics tests."""
    db_path = tmp_path / "test_analytics.db"
    connection = sqlite3.connect(db_path)

    connection.executescript(
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
        );

        CREATE TABLE test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    connection.commit()
    connection.close()

    monkeypatch.setattr(analytics, "DATABASE_PATH", str(db_path))
    return str(db_path)


def insert_run(db_path, results):
    """Insert one test run and its test results."""
    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO test_runs DEFAULT VALUES")
        run_id = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO test_results
                (test_name, status, duration, error, category,
                 created_at, run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    name,
                    status,
                    duration,
                    error,
                    category,
                    "2026-10-24 10:00:00",
                    run_id,
                )
                for name, status, duration, error, category in results
            ],
        )

        connection.commit()
        return run_id
    finally:
        connection.close()


def test_analytics_count_latest_run(test_db):
    insert_run(
        test_db,
        [
            ("test_old", "passed", 0.1, "", ""),
        ],
    )

    latest_run_id = insert_run(
        test_db,
        [
            ("test_login", "passed", 0.1, "", ""),
            (
                "test_payment",
                "failed",
                0.2,
                "AssertionError",
                "Assertion Failure",
            ),
        ],
    )

    stats = analytics.get_test_statistics()

    assert stats["run_id"] == latest_run_id
    assert stats["total"] == 2
    assert stats["passed"] == 1
    assert stats["failed"] == 1
    assert stats["expected_failures"] == 0
    assert stats["pass_percentage"] == 50.0


def test_expected_failures_are_excluded_from_pass_rate(test_db):
    run_id = insert_run(
        test_db,
        [
            ("test_login", "passed", 0.1, "", ""),
            ("test_payment", "failed", 0.2, "Error", "Assertion Failure"),
            ("test_known_issue", "xfailed", 0.1, "Known issue", "Timeout"),
        ],
    )

    stats = analytics.get_test_statistics()

    assert stats["run_id"] == run_id
    assert stats["total"] == 3
    assert stats["passed"] == 1
    assert stats["failed"] == 1
    assert stats["expected_failures"] == 1
    assert stats["pass_percentage"] == 50.0


def test_all_passed_tests_have_100_percent_pass_rate(test_db):
    insert_run(
        test_db,
        [
            ("test_login", "passed", 0.1, "", ""),
            ("test_search", "passed", 0.2, "", ""),
        ],
    )

    stats = analytics.get_test_statistics()

    assert stats["total"] == 2
    assert stats["passed"] == 2
    assert stats["failed"] == 0
    assert stats["pass_percentage"] == 100.0


def test_empty_database_returns_zero_statistics(test_db):
    stats = analytics.get_test_statistics()

    assert stats["run_id"] is None
    assert stats["total"] == 0
    assert stats["passed"] == 0
    assert stats["failed"] == 0
    assert stats["expected_failures"] == 0
    assert stats["pass_percentage"] == 0
    assert stats["failure_categories"] == []


def test_failure_categories_are_counted(test_db):
    insert_run(
        test_db,
        [
            ("test_a", "failed", 0.1, "Error A", "Timeout"),
            ("test_b", "failed", 0.2, "Error B", "Timeout"),
            ("test_c", "xfailed", 0.1, "Known issue", "Assertion Failure"),
            ("test_d", "passed", 0.1, "", ""),
        ],
    )

    stats = analytics.get_test_statistics()

    assert stats["failure_categories"] == [
        ("Timeout", 2),
        ("Assertion Failure", 1),
    ]


def test_history_is_chronological_and_calculates_pass_rate(test_db):
    first_run = insert_run(
        test_db,
        [
            ("test_a", "passed", 0.1, "", ""),
            ("test_b", "failed", 0.2, "Error", "Timeout"),
        ],
    )

    second_run = insert_run(
        test_db,
        [
            ("test_c", "passed", 0.1, "", ""),
            ("test_d", "passed", 0.2, "", ""),
            ("test_e", "xfailed", 0.1, "Known issue", "Timeout"),
        ],
    )

    history = analytics.get_test_history()

    assert [run["run_id"] for run in history] == [
        first_run,
        second_run,
    ]

    assert history[0]["total"] == 2
    assert history[0]["pass_percentage"] == 50

    assert history[1]["total"] == 3
    assert history[1]["expected_failures"] == 1
    assert history[1]["pass_percentage"] == 100


def test_history_respects_limit(test_db):
    for _ in range(3):
        insert_run(
            test_db,
            [("test_login", "passed", 0.1, "", "")],
        )

    history = analytics.get_test_history(limit=2)

    assert len(history) == 2
    assert history[0]["run_id"] < history[1]["run_id"]
