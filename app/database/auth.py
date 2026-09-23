"""
Simple username/password authentication using bcrypt password hashing.
Users are stored in the same SQLite database as the rest of the app.
"""

import sqlite3
from pathlib import Path

import bcrypt

DB_PATH = Path(__file__).resolve().parent / "library.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_users_table():
    """Create the users table if it doesn't already exist. Safe to call every startup."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "That username is already taken."

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    conn.commit()
    conn.close()
    return True, "Account created successfully."


def verify_user(username: str, password: str) -> bool:
    """Check if a username/password combination is valid."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row[0].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

def init_chat_history_table():
    """Create the chat_history table if it doesn't already exist."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(username: str, role: str, content: str, tool_calls: list = None):
    """Save one chat message to persistent history."""
    import json
    conn = _connect()
    cursor = conn.cursor()
    tool_calls_json = json.dumps(tool_calls) if tool_calls else None
    cursor.execute(
        "INSERT INTO chat_history (username, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (username, role, content, tool_calls_json),
    )
    conn.commit()
    conn.close()


def load_chat_history(username: str) -> list[dict]:
    """Load all past messages for a user, in order."""
    import json
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, tool_calls FROM chat_history WHERE username = ? ORDER BY id",
        (username,),
    )
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = {"role": row["role"], "content": row["content"]}
        if row["tool_calls"]:
            msg["tool_calls"] = json.loads(row["tool_calls"])
        messages.append(msg)
    return messages


def clear_chat_history(username: str):
    """Delete all chat history for a user."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    
def init_rate_limit_table():
    """Create the rate_limits table if it doesn't already exist."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def check_and_record_rate_limit(username: str, max_requests: int = 10, window_minutes: int = 5) -> tuple[bool, str]:
    """
    Check if a user is within their rate limit. If allowed, records this request.
    Returns (allowed: bool, message: str).
    """
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) FROM rate_limits
        WHERE username = ?
        AND requested_at >= datetime('now', ?)
        """,
        (username, f"-{window_minutes} minutes"),
    )
    recent_count = cursor.fetchone()[0]

    if recent_count >= max_requests:
        conn.close()
        return False, (
            f"Rate limit reached: max {max_requests} requests per {window_minutes} minutes. "
            "Please wait a moment before trying again."
        )

    cursor.execute("INSERT INTO rate_limits (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()
    return True, ""