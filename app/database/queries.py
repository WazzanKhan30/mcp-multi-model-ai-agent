"""
Safe, read-only query functions for our library database.
No arbitrary SQL is ever accepted from the LLM — only these
specific, parameterized functions.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "library.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def list_all_books() -> list[dict]:
    """List all books in the library database."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT title, author, genre, year, rating FROM books ORDER BY rating DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def search_books_by_genre(genre: str) -> list[dict]:
    """Search books by genre (e.g. 'Fantasy', 'Science Fiction')."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, author, genre, year, rating FROM books WHERE genre LIKE ? ORDER BY rating DESC",
        (f"%{genre}%",),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def search_books_by_author(author: str) -> list[dict]:
    """Search books by author name (partial match allowed)."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, author, genre, year, rating FROM books WHERE author LIKE ? ORDER BY year",
        (f"%{author}%",),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_top_rated_books(limit: int = 5) -> list[dict]:
    """Get the top-rated books, sorted by rating (highest first)."""
    if limit > 20:
        limit = 20
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, author, genre, year, rating FROM books ORDER BY rating DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows