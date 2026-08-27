"""
Unit tests for the calculator tool logic.
These test the plain Python functions directly (not through MCP),
since the business logic and the MCP wrapping are separate concerns.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mcp_server.tools import calculator


def test_add():
    assert calculator.add(2, 3) == 5
    assert calculator.add(-1, 1) == 0
    assert calculator.add(2.5, 2.5) == 5.0


def test_subtract():
    assert calculator.subtract(10, 4) == 6
    assert calculator.subtract(4, 10) == -6


def test_multiply():
    assert calculator.multiply(3, 4) == 12
    assert calculator.multiply(-2, 5) == -10


def test_divide():
    assert calculator.divide(10, 2) == 5
    assert calculator.divide(7, 2) == 3.5


def test_divide_by_zero_raises_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10, 0)


def test_percentage_of():
    assert calculator.percentage_of(25, 8000) == 2000
    assert calculator.percentage_of(50, 200) == 100


def test_what_percentage():
    assert calculator.what_percentage(25, 8000) == 0.3125
    assert calculator.what_percentage(50, 200) == 25


def test_what_percentage_whole_zero_raises_error():
    with pytest.raises(ValueError, match="Whole cannot be zero"):
        calculator.what_percentage(10, 0)


def test_average():
    assert calculator.average([10, 20, 30]) == 20
    assert calculator.average([4.7, 4.7, 4.7]) == 4.7


def test_average_empty_list_raises_error():
    with pytest.raises(ValueError, match="Cannot average an empty list"):
        calculator.average([])