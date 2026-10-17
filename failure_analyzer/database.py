import sqlite3
from pathlib import Path

DATABASE_PATH = Path("reports") / "testsense.db"


def create_database():
    """
    Create the database and the test_results table.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                status TEXT NOT NULL,
                duration REAL DEFAULT 0,
                error TEXT,
                traceback TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add run_id to existing database without deleting records.
        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA  table_info(test_results)"
            ).fetchall()
        }

        if "run_id" not in columns:
            cursor.execute(
                "ALTER TABLE test_results ADD COLUMN run_id INTEGER"
            )

        connection.commit()
        print(f"Database created successfully: {DATABASE_PATH}")

    finally:
        connection.close()

def create_test_run():
    """Create and return a unique ID  for a test execution run."""
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO test_runs DEFAULT VALUES")
        connection.commit()

        run_id = cursor.lastrowid
        print(f"Created test run: {run_id}")
        return run_id

    finally:
        connection.close()

def save_test_result(
        test_name,
        status,
        duration=0,
        error="",
        traceback="",
        category="",
        run_id=None
):
    """
    Save one test result to the SQLite database.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO test_results (
                test_name, 
                status, 
                duration, 
                error, 
                traceback, 
                category,
                run_id
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (
            test_name,
            status,
            duration,
            error,
            traceback,
            category,
            run_id,
        ))

        connection.commit()
        print(f"Saved test result: {test_name}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_database()

    save_test_result(
        test_name="tests/test_login.py::test_invalid_login",
        status="failed",
        duration=0.15,
        error="AssertionError",
        traceback="Expected admin123 but received wrong",
        category="Assertion Failure"
    )
