"""
The core agent loop: takes a user message, talks to the LLM + MCP tools,
chains multiple tool calls if needed, and returns a final answer.

Can open its own short-lived MCP connection (default - used by tests
and standalone scripts), or reuse an already-connected client passed
in via `mcp_client` (used by the Streamlit app's persistent connection,
to avoid spawning a new subprocess for every single request).
"""

import os
import sys
import time
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.logger import get_logger

logger = get_logger("agent")

SERVER_SCRIPT = str(Path(__file__).resolve().parents[1] / "mcp_server" / "server.py")

MAX_TOOL_ROUNDS = 10


def get_llm_provider():
    """Select the LLM provider based on the LLM_PROVIDER env variable."""
    provider_name = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider_name == "openrouter":
        return OpenRouterProvider()
    return GroqProvider()


async def run_agent(user_message: str, mcp_client=None) -> dict:
    """
    Runs one full agent turn. If mcp_client is provided, reuses that
    existing connection. Otherwise opens and closes its own short-lived
    connection (used by tests/scripts that don't manage a persistent one).
    """
    if mcp_client is not None:
        return await _run_agent_loop(user_message, mcp_client)

    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])
    async with Client(stdio_client(server_params)) as mcp_client:
        return await _run_agent_loop(user_message, mcp_client)


async def _run_agent_loop(user_message: str, mcp_client) -> dict:
    provider_name = os.environ.get("LLM_PROVIDER", "groq").lower()
    logger.info(f"New request | provider={provider_name} | message={user_message!r}")

    request_start = time.monotonic()
    tool_call_log = []

    tools_result = await mcp_client.list_tools()
    provider = get_llm_provider()

    messages = [{"role": "user", "content": user_message}]

    for round_num in range(MAX_TOOL_ROUNDS):
        try:
            decision = provider.generate(messages, tools_result.tools)
        except Exception as e:
            logger.error(
                f"LLM call failed | provider={provider_name} | round={round_num} | error={e}"
            )
            return {
                "answer": (
                    "I couldn't complete this request because the AI model provider "
                    "had an issue (this is often temporary — please try again). "
                    f"Technical detail: {type(e).__name__}."
                ),
                "tool_calls": tool_call_log,
            }

        if decision["type"] == "text":
            elapsed = time.monotonic() - request_start
            logger.info(
                f"Request complete | rounds={round_num} | tool_calls={len(tool_call_log)} "
                f"| total_time={elapsed:.2f}s"
            )
            return {
                "answer": decision["text"],
                "tool_calls": tool_call_log,
            }

        tool_name = decision["name"]
        tool_args = decision["arguments"]
        tool_start = time.monotonic()

        logger.info(f"Tool call requested | tool={tool_name} | args={tool_args}")

        try:
            result = await mcp_client.call_tool(tool_name, tool_args)
            tool_elapsed = time.monotonic() - tool_start
            if result.is_error:
                tool_output = f"Error: {result.content[0].text}"
                logger.warning(
                    f"Tool call failed | tool={tool_name} | time={tool_elapsed:.2f}s | {tool_output}"
                )
            else:
                tool_output = str(result.structured_content)
                logger.info(
                    f"Tool call succeeded | tool={tool_name} | time={tool_elapsed:.2f}s"
                )
        except Exception as e:
            tool_output = f"Error calling tool: {e}"
            logger.error(f"Tool call exception | tool={tool_name} | error={e}")

        tool_call_log.append(
            {"tool": tool_name, "arguments": tool_args, "result": tool_output}
        )

        messages.append(decision["raw_message"])
        messages.append(
            {
                "role": "tool",
                "tool_call_id": decision["tool_call_id"],
                "content": tool_output,
            }
        )

    elapsed = time.monotonic() - request_start
    logger.warning(f"Max tool rounds reached | tool_calls={len(tool_call_log)} | total_time={elapsed:.2f}s")
    return {
        "answer": "I wasn't able to complete this request within the allowed number of tool calls.",
        "tool_calls": tool_call_log,
    }