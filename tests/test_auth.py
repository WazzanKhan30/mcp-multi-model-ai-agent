"""
Unit tests for the authentication module.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import auth


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    auth.init_users_table()
    yield
    # Clean up any test users created
    conn = auth._connect()
    conn.execute("DELETE FROM users WHERE username LIKE 'test_%'")
    conn.commit()
    conn.close()


def test_register_new_user_succeeds():
    success, message = auth.register_user("test_alice", "password123")
    assert success is True


def test_register_duplicate_username_fails():
    auth.register_user("test_bob", "password123")
    success, message = auth.register_user("test_bob", "differentpassword")
    assert success is False
    assert "already taken" in message


def test_register_short_password_fails():
    success, message = auth.register_user("test_charlie", "123")
    assert success is False


def test_verify_correct_password():
    auth.register_user("test_dave", "correctpassword")
    assert auth.verify_user("test_dave", "correctpassword") is True


def test_verify_wrong_password_fails():
    auth.register_user("test_eve", "correctpassword")
    assert auth.verify_user("test_eve", "wrongpassword") is False


def test_verify_nonexistent_user_fails():
    assert auth.verify_user("test_nobody", "anypassword") is False