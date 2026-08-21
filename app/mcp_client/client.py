"""
Standalone MCP client test — connects to our server as a subprocess,
lists its tools, and calls one. No LLM involved yet; this just proves
the client <-> server plumbing works on its own.
"""

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = str(Path(__file__).resolve().parents[2] / "app" / "mcp_server" / "server.py")


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
    )

    # Pass the transport (an un-entered async context manager) directly to Client.
    # Client itself enters it internally — we don't open it ourselves.
    async with Client(stdio_client(server_params)) as client:
        print(f"Connected. Protocol version: {client.protocol_version}")

        tools_result = await client.list_tools()
        print("\nAvailable tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

        result = await client.call_tool("add", {"a": 15, "b": 27})
        print(f"\nCalled add(15, 27) -> is_error={result.is_error}")
        print(f"Structured result: {result.structured_content}")

        error_result = await client.call_tool("divide", {"a": 10, "b": 0})
        print(f"\nCalled divide(10, 0) -> is_error={error_result.is_error}")
        for block in error_result.content:
            if hasattr(block, "text"):
                print(f"Error message: {block.text}")


if __name__ == "__main__":
    asyncio.run(main())