import sqlite3
from pathlib import Path

DATABSE_PATH = Path("reports") / "testsense.db"


def create_database():
    """
    Create the database and the test_results table.
    """
    DATABSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABSE_PATH)

    try:
        cursor = connection.cursor()

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
        connection.commit()
        print(f"Database created successfully: {DATABSE_PATH}")
    finally:
        connection.close()


def save_test_result(
        test_name,
        status,
        duration=0,
        error="",
        traceback="",
        category=""):
    """
    Save one test result to the SQLite database.
    """
    DATABSE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABSE_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO test_results (
                test_name, 
                status, 
                duration, 
                error, 
                traceback, 
                category
            )
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            test_name,
            status,
            duration,
            error,
            traceback,
            category
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
