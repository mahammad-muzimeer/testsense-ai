import sqlite3
from failure_analyzer.analytics import get_test_statistics
from failure_analyzer.database import DATABASE_PATH


def test_analytics_count_latest_run():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO test_runs DEFAULT VALUES"
        )
        run_id = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO test_results
                (test_name, status, duration, error, category, run_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("test_login", "passed", 0.1, "", "", run_id),
                (
                    "test_payment",
                    "failed",
                    0.2,
                    "AssertionError",
                    "Assertion Failure",
                    run_id,
                ),
            ],
        )
        connection.commit()

    finally:
        connection.close()

    stats = get_test_statistics()

    assert stats["run_id"] == run_id
    assert stats["total"] == 2
    assert stats["passed"] == 1
    assert stats["failed"] == 1
    assert stats["pass_percentage"] == 50.0
