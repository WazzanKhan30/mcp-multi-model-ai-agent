"""
Lightweight metrics tracking: records key numbers about each request
(latency, tool used, success/failure) to SQLite, and provides simple
aggregate queries for a dashboard.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "library.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_metrics_table():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            total_time_seconds REAL,
            tool_call_count INTEGER,
            provider TEXT,
            success INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def record_request(username: str, total_time: float, tool_call_count: int, provider: str, success: bool):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO request_metrics (username, total_time_seconds, tool_call_count, provider, success)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, total_time, tool_call_count, provider, 1 if success else 0),
    )
    conn.commit()
    conn.close()


def get_summary_stats() -> dict:
    """Return aggregate stats across all requests, for a dashboard."""
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM request_metrics")
    total_requests = cursor.fetchone()[0]

    if total_requests == 0:
        conn.close()
        return {
            "total_requests": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "avg_tool_calls": 0,
        }

    cursor.execute("SELECT AVG(success) FROM request_metrics")
    success_rate = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(total_time_seconds) FROM request_metrics")
    avg_time = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(tool_call_count) FROM request_metrics")
    avg_tools = cursor.fetchone()[0] or 0

    conn.close()
    return {
        "total_requests": total_requests,
        "success_rate": round(success_rate * 100, 1),
        "avg_response_time": round(avg_time, 2),
        "avg_tool_calls": round(avg_tools, 2),
    }