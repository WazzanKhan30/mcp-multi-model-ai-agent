"""
One-time script to create and seed our local SQLite database.
Run this once to generate app/database/library.db.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "library.db"

SAMPLE_BOOKS = [
    ("Dune", "Frank Herbert", "Science Fiction", 1965, 4.8),
    ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 1937, 4.7),
    ("1984", "George Orwell", "Dystopian", 1949, 4.9),
    ("Foundation", "Isaac Asimov", "Science Fiction", 1951, 4.6),
    ("Neuromancer", "William Gibson", "Cyberpunk", 1984, 4.3),
    ("Brave New World", "Aldous Huxley", "Dystopian", 1932, 4.6),
    ("The Name of the Wind", "Patrick Rothfuss", "Fantasy", 2007, 4.7),
    ("Snow Crash", "Neal Stephenson", "Cyberpunk", 1992, 4.2),
    ("Project Hail Mary", "Andy Weir", "Science Fiction", 2021, 4.9),
    ("Mistborn", "Brandon Sanderson", "Fantasy", 2006, 4.7),
]


def create_and_seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO books (title, author, genre, year, rating) VALUES (?, ?, ?, ?, ?)",
            SAMPLE_BOOKS,
        )
        print(f"Inserted {len(SAMPLE_BOOKS)} sample books.")
    else:
        print("Database already has data, skipping seed.")

    conn.commit()
    conn.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    create_and_seed()
    