"""
Thin wrapper around the Groq API for our agent.
Converts MCP tool schemas into Groq's (OpenAI-compatible) function format,
and translates Groq's responses into a simple, provider-agnostic shape.
"""

import os
import json
from groq import Groq


class GroqProvider:
    def __init__(self):
        api_key = os.environ["GROQ_API_KEY"]
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def _mcp_tools_to_groq_format(self, mcp_tools):
        """Convert MCP tool definitions into Groq/OpenAI-style tool dicts."""
        tools = []
        for tool in mcp_tools:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
            )
        return tools

    def generate(self, user_message: str, mcp_tools: list):
        """
        Send a message to Groq along with available MCP tools.
        Returns either a text response or a requested tool call.
        """
        groq_tools = self._mcp_tools_to_groq_format(mcp_tools)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": user_message}],
            tools=groq_tools,
            tool_choice="auto",
            temperature=0,  # deterministic-ish, best for tool calling
        )

        message = response.choices[0].message

        if message.tool_calls:
            call = message.tool_calls[0]  # first tool call for now
            return {
                "type": "tool_call",
                "name": call.function.name,
                "arguments": json.loads(call.function.arguments),
            }
        else:
            return {"type": "text", "text": message.content}