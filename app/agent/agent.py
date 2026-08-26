"""
The core agent loop: takes a user message, talks to the LLM + MCP tools,
chains multiple tool calls if needed, and returns a final answer.
"""

import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

import os
from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider


def get_llm_provider():
    """Select the LLM provider based on the LLM_PROVIDER env variable."""
    provider_name = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider_name == "openrouter":
        return OpenRouterProvider()
    return GroqProvider()  # default

SERVER_SCRIPT = str(Path(__file__).resolve().parents[1] / "mcp_server" / "server.py")

MAX_TOOL_ROUNDS = 10  # safety limit so a confused model can't loop forever  # safety limit so a confused model can't loop forever


async def run_agent(user_message: str) -> dict:
    """
    Runs one full agent turn. Returns a dict with the final answer text
    and a log of every tool call made along the way (for UI display later).
    """
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])
    tool_call_log = []

    async with Client(stdio_client(server_params)) as mcp_client:
        tools_result = await mcp_client.list_tools()
        provider = get_llm_provider()

        messages = [{"role": "user", "content": user_message}]

        for _ in range(MAX_TOOL_ROUNDS):
            decision = provider.generate(messages, tools_result.tools)

            if decision["type"] == "text":
                return {
                    "answer": decision["text"],
                    "tool_calls": tool_call_log,
                }

            # It's a tool call: execute via the real MCP client
            tool_name = decision["name"]
            tool_args = decision["arguments"]

            try:
                result = await mcp_client.call_tool(tool_name, tool_args)
                if result.is_error:
                    tool_output = f"Error: {result.content[0].text}"
                else:
                    tool_output = str(result.structured_content)
            except Exception as e:
                tool_output = f"Error calling tool: {e}"

            tool_call_log.append(
                {"tool": tool_name, "arguments": tool_args, "result": tool_output}
            )

            # Append the assistant's tool-call message, then the tool's result,
            # so the LLM sees both on the next loop iteration.
            messages.append(decision["raw_message"])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": decision["tool_call_id"],
                    "content": tool_output,
                }
            )

        # Safety fallback if the model never stops calling tools
        return {
            "answer": "I wasn't able to complete this request within the allowed number of tool calls.",
            "tool_calls": tool_call_log,
        }