
import sqlite3

from failure_analyzer.database import DATABASE_PATH


def get_test_statistics():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        # Find the most recent run that has saved test results.
        cursor.execute("""
            SELECT MAX(run_id)
            FROM test_results
            WHERE run_id IS NOT NULL
        """)
        latest_run_id = cursor.fetchone()[0]

        # Fall back to all historical records if no run has been tracked yet.
        if latest_run_id is None:
            cursor.execute("""
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                FROM test_results
            """)
        else:
            cursor.execute("""
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                FROM test_results
                WHERE run_id = ?
            """, (latest_run_id,))

        total, passed, failed = cursor.fetchone()

        total = total or 0
        passed = passed or 0
        failed = failed or 0

        pass_percentage = round(
            passed / total * 100 if total else 0,
            2,
        )

        if latest_run_id is None:
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM test_results
                WHERE status = 'failed'
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """)
        else:
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM test_results
                WHERE status = 'failed' AND run_id = ?
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """, (latest_run_id,))

        failure_categories = cursor.fetchall()

        return {
            "run_id": latest_run_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_percentage": pass_percentage,
            "failure_categories": failure_categories,
        }

    finally:
        connection.close()


if __name__ == "__main__":
    print(get_test_statistics())
