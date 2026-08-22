"""
Thin wrapper around the Groq API for our agent.
Converts MCP tool schemas into Groq's (OpenAI-compatible) function format,
and translates Groq's responses into a simple, provider-agnostic shape.
Supports full conversation history so multi-step tool chaining works.
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

    def generate(self, messages: list, mcp_tools: list):
        """
        Send full conversation history to Groq along with available MCP tools.
        Returns either a text response or a requested tool call, PLUS the raw
        assistant message (needed to append correctly to history for the next turn).
        """
        groq_tools = self._mcp_tools_to_groq_format(mcp_tools)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            temperature=0,
        )

        message = response.choices[0].message

        if message.tool_calls:
            call = message.tool_calls[0]
            return {
                "type": "tool_call",
                "name": call.function.name,
                "arguments": json.loads(call.function.arguments),
                "tool_call_id": call.id,
                "raw_message": message,
            }
        else:
            return {
                "type": "text",
                "text": message.content,
                "raw_message": message,
            }