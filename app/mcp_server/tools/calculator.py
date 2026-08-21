"""
Calculator tool for the MCP server.
Provides basic arithmetic operations the LLM can call.
"""


def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b. Raises an error if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


def percentage(part: float, whole: float) -> float:
    """Calculate what percentage 'part' is of 'whole'."""
    if whole == 0:
        raise ValueError("Whole cannot be zero.")
    return (part / whole) * 100


def average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot average an empty list.")
    return sum(numbers) / len(numbers)