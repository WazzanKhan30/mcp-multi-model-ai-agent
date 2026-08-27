"""
Integration tests for the MCP client <-> server connection.
These spin up the real MCP server as a subprocess and talk to it
over the real STDIO transport - genuine protocol-level testing,
not mocked.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = str(Path(__file__).resolve().parents[1] / "app" / "mcp_server" / "server.py")


@pytest.fixture
def server_params():
    return StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])


@pytest.mark.asyncio
async def test_tool_discovery_returns_all_expected_tools(server_params):
    async with Client(stdio_client(server_params)) as client:
        result = await client.list_tools()
        tool_names = {tool.name for tool in result.tools}

        expected_tools = {
            "add", "subtract", "multiply", "divide", "average",
            "percentage_of", "what_percentage",
            "get_weather",
            "search_github_repos", "get_github_repo_stats",
            "list_all_books", "search_books_by_genre",
            "search_books_by_author", "get_top_rated_books",
            "search_web",
        }
        assert expected_tools.issubset(tool_names)


@pytest.mark.asyncio
async def test_call_add_tool_via_mcp(server_params):
    async with Client(stdio_client(server_params)) as client:
        result = await client.call_tool("add", {"a": 15, "b": 27})
        assert result.is_error is False
        assert result.structured_content["result"] == 42.0


@pytest.mark.asyncio
async def test_call_divide_by_zero_returns_error_not_crash(server_params):
    async with Client(stdio_client(server_params)) as client:
        result = await client.call_tool("divide", {"a": 10, "b": 0})
        assert result.is_error is True


@pytest.mark.asyncio
async def test_call_unknown_tool_returns_error(server_params):
    async with Client(stdio_client(server_params)) as client:
        result = await client.call_tool("this_tool_does_not_exist", {})
        assert result.is_error is True


@pytest.mark.asyncio
async def test_call_database_tool_via_mcp(server_params):
    async with Client(stdio_client(server_params)) as client:
        result = await client.call_tool("search_books_by_genre", {"genre": "Fantasy"})
        assert result.is_error is False
        assert len(result.structured_content["result"]) == 3
        