
import sqlite3

from failure_analyzer.database import DATABASE_PATH


def get_test_statistics():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        # Find the latest test run.
        cursor.execute("""
            SELECT MAX(run_id)
            FROM test_results
            WHERE run_id IS NOT NULL
        """)
        latest_run_id = cursor.fetchone()[0]

        # Build the query for the latest run.
        if latest_run_id is None:
            query = """
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'xfailed' THEN 1 ELSE 0 END)
                FROM test_results
            """
            cursor.execute(query)
        else:
            query = """
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'xfailed' THEN 1 ELSE 0 END)
                FROM test_results
                WHERE run_id = ?
            """
            cursor.execute(query, (latest_run_id,))

        total, passed, failed, expected_failures = cursor.fetchone()

        total = total or 0
        passed = passed or 0
        failed = failed or 0
        expected_failures = expected_failures or 0

        # Exclude expected failures from the pass-rate denominator.
        completed_tests = passed + failed
        pass_percentage = round(
            passed / completed_tests * 100 if completed_tests else 0,
            2,
        )

        # Include expected failures in the category chart.
        if latest_run_id is None:
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM test_results
                WHERE status IN ('failed', 'xfailed')
                  AND category IS NOT NULL
                  AND category != ''
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """)
        else:
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM test_results
                WHERE run_id = ?
                  AND status IN ('failed', 'xfailed')
                  AND category IS NOT NULL
                  AND category != ''
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """, (latest_run_id,))

        failure_categories = cursor.fetchall()

        return {
            "run_id": latest_run_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "expected_failures": expected_failures,
            "pass_percentage": pass_percentage,
            "failure_categories": failure_categories,
        }

    finally:
        connection.close()


if __name__ == "__main__":
    print(get_test_statistics())
