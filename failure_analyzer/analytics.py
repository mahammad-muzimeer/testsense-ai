import sqlite3
from failure_analyzer.database import DATABASE_PATH


def get_test_statistics():
    conn = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
            FROM test_results
        """)

        total, passed, failed = cursor.fetchone()

        total = total or 0
        passed = passed or 0
        failed = failed or 0

        pass_percentage = (
            passed / total * 100 if total else 0
        )

        cursor.execute("""
            SELECT category, COUNT(*) AS occurrences
            FROM test_results
            WHERE status = 'failed'
            GROUP BY category
            ORDER BY occurrences DESC
        """)

        failure_categories = cursor.fetchall()

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_percentage": round(pass_percentage, 2),
            "failure_categories": failure_categories,
        }

    finally:
        conn.close()


def main():
    stats = get_test_statistics()

    print("\n=== TestSense AI: Test Statistics ===")
    print(f"Total recorded results  : {stats['total']}")
    print(f"Passed                  : {stats['passed']}")
    print(f"Failed                  : {stats['failed']}")
    print(f"Pass percentage         : {stats['pass_percentage']}")

    print("\nFailure categories:")
    if stats["failure_categories"]:
        for category, count in stats["failure_categories"]:
            print(f"{category or 'Unclassified'}: {count}")
    else:
        print("No failure recorded.")


if __name__ == "__main__":
    main()