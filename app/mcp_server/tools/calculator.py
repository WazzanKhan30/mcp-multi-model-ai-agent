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


def percentage_of(percent: float, whole: float) -> float:
    """Calculate a percentage of a number. E.g. 25% of 8000 = percent=25, whole=8000 -> 2000."""
    return (percent / 100) * whole


def what_percentage(part: float, whole: float) -> float:
    """Calculate what percentage 'part' is of 'whole'. E.g. 25 is what % of 8000 -> part=25, whole=8000 -> 0.3125."""
    if whole == 0:
        raise ValueError("Whole cannot be zero.")
    return (part / whole) * 100


def average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot average an empty list.")
    return sum(numbers) / len(numbers)