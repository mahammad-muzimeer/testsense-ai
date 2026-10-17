import sqlite3
from fastapi import FastAPI, HTTPException
from failure_analyzer.database import DATABASE_PATH
from failure_analyzer.analytics import get_test_statistics

app = FastAPI(
    title="TestSense API",
    description="Automated test failure analysis API",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to TestSense API",
        "status": "running"
    }

@app.get("/analytics")
def analytics():
    return get_test_statistics()

@app.get("/results")
def get_results(limit: int = 20):
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT MAX(run_id)
            FROM test_results
            WHERE run_id is NOT NULL
            """
        )
        latest_run_id = cursor.fetchone()[0]

        if latest_run_id is None:
            cursor.execute(
                """
                SELECT id, test_name, status, duration,
                       error, category, created_at
                FROM test_results
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cursor.execute(
                """
                SELECT id, test_name, status, duration,
                       error, category, created_at, run_id
                FROM test_results
                WHERE run_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (latest_run_id, limit,),
            )
        return {
            "run_id": latest_run_id,
            "results": [dict(row) for row in cursor.fetchall()],
        }

    finally:
        connection.close()
