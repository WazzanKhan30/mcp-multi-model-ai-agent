"""
Unit tests for the database query functions.
Tests run against the real library.db (read-only queries, so safe).
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import queries as db_queries


def test_list_all_books_returns_ten_books():
    books = db_queries.list_all_books()
    assert len(books) == 10
    assert all("title" in book for book in books)


def test_list_all_books_sorted_by_rating_descending():
    books = db_queries.list_all_books()
    ratings = [book["rating"] for book in books]
    assert ratings == sorted(ratings, reverse=True)


def test_search_books_by_genre_fantasy():
    books = db_queries.search_books_by_genre("Fantasy")
    assert len(books) == 3
    titles = {book["title"] for book in books}
    assert "The Hobbit" in titles
    assert "Mistborn" in titles


def test_search_books_by_genre_case_insensitive_partial_match():
    books = db_queries.search_books_by_genre("fantasy")  # lowercase
    assert len(books) == 3


def test_search_books_by_genre_no_match_returns_empty():
    books = db_queries.search_books_by_genre("Nonexistent Genre")
    assert books == []


def test_search_books_by_author():
    books = db_queries.search_books_by_author("Tolkien")
    assert len(books) == 1
    assert books[0]["title"] == "The Hobbit"


def test_get_top_rated_books_default_limit():
    books = db_queries.get_top_rated_books()
    assert len(books) == 5


def test_get_top_rated_books_custom_limit():
    books = db_queries.get_top_rated_books(limit=3)
    assert len(books) == 3


def test_get_top_rated_books_limit_capped_at_twenty():
    books = db_queries.get_top_rated_books(limit=1000)
    assert len(books) == 10  # only 10 books exist total, so capped naturally