import sqlite3
from failure_analyzer.database import DATABASE_PATH

def view_results():
    conn = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, test_name, status, category, duration
            FROM test_results
            ORDER BY id
            LIMIT 20
            """
        )

        rows = cursor.fetchall()

        print("\n--- TestSense AI: Stored Test Results ---")

        if not rows:
            print("No test results found.")
            return

        for row in rows:
            result_id, test_name, status, category, duration = row

            print(f"\nID          : {result_id}")
            print(f"Test        : {test_name}")
            print(f"Status      : {status}")
            print(f"Category    : {category or '-'}")
            print(f"Duration    : {duration:.2f} seconds")

    finally:
        conn.close()


if __name__ == "__main__":
    view_results()
