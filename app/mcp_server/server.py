"""
MCP Server — exposes our tools (starting with calculator) to any MCP client.
"""

import sys
from pathlib import Path

# Make sure the project root is on Python's import path, so "app.xxx" imports work
# no matter how this file is launched (directly, via mcp dev, etc.)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mcp.server import MCPServer
from app.mcp_server.tools import calculator, weather, github
from app.database import queries as db_queries

# Create the server instance. The name shows up in MCP clients/inspectors.
mcp = MCPServer("MCP Agent Server")

# Create the server instance. The name shows up in MCP clients/inspectors.
mcp = MCPServer("MCP Agent Server")


# Each @mcp.tool() decorator turns a plain function into an MCP tool.
# The SDK reads the function's type hints and docstring to auto-generate
# the schema an LLM will see (name, description, parameters) — no manual
# JSON schema writing needed.

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return calculator.add(a, b)


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return calculator.subtract(a, b)


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return calculator.multiply(a, b)


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    return calculator.divide(a, b)





@mcp.tool()
def percentage_of(percent: float, whole: float) -> float:
    """Calculate a percentage of a number. E.g. 25% of 8000 = percent=25, whole=8000 -> 2000."""
    return calculator.percentage_of(percent, whole)


@mcp.tool()
def what_percentage(part: float, whole: float) -> float:
    """Calculate what percentage 'part' is of 'whole'. E.g. 25 is what % of 8000 -> part=25, whole=8000 -> 0.3125."""
    return calculator.what_percentage(part, whole)


@mcp.tool()
def average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers."""
    return calculator.average(numbers)

@mcp.tool()
def get_weather(city: str) -> dict:
    """Get the current weather (temperature, wind, condition) for a given city."""
    return weather.get_current_weather(city)


@mcp.tool()
def search_github_repos(query: str, limit: int = 5) -> list[dict]:
    """Search GitHub repositories by keyword, sorted by stars (most popular first)."""
    return github.search_repositories(query, limit)


@mcp.tool()
def get_github_repo_stats(owner: str, repo: str) -> dict:
    """Get statistics (stars, forks, open issues) for a specific GitHub repository."""
    return github.get_repository_stats(owner, repo)


@mcp.tool()
def list_all_books() -> list[dict]:
    """List all books in the library database, sorted by rating."""
    return db_queries.list_all_books()


@mcp.tool()
def search_books_by_genre(genre: str) -> list[dict]:
    """Search the library database for books in a specific genre."""
    return db_queries.search_books_by_genre(genre)


@mcp.tool()
def search_books_by_author(author: str) -> list[dict]:
    """Search the library database for books by a specific author."""
    return db_queries.search_books_by_author(author)


@mcp.tool()
def get_top_rated_books(limit: int = 5) -> list[dict]:
    """Get the top-rated books from the library database."""
    return db_queries.get_top_rated_books(limit)


if __name__ == "__main__":
    mcp.run()