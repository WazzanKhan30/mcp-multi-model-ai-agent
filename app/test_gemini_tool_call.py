"""
Phase 5 test: one full round of Gemini deciding to call a real MCP tool.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.llm.groq_provider import GroqProvider

SERVER_SCRIPT = str(Path(__file__).resolve().parent / "mcp_server" / "server.py")


async def main():
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with Client(stdio_client(server_params)) as mcp_client:
        tools_result = await mcp_client.list_tools()

        groq = GroqProvider()

        user_message = "What is 25% of 8000?"
        print(f"User: {user_message}\n")

        decision = groq.generate(user_message, tools_result.tools)
        print(f"Groq's decision: {decision}\n")

        if decision["type"] == "tool_call":
            result = await mcp_client.call_tool(decision["name"], decision["arguments"])
            print(f"Tool '{decision['name']}' executed via MCP.")
            print(f"Result: {result.structured_content}")
        else:
            print(f"Groq answered directly: {decision['text']}")


if __name__ == "__main__":
    asyncio.run(main())