"""
Thin wrapper around OpenRouter (OpenAI-compatible API) for our agent.
Serves as our second LLM provider, demonstrating true multi-provider support.
"""

import os
import json
from urllib import response
from openai import OpenAI


class OpenRouterProvider:
    def __init__(self):
        api_key = os.environ["OPENROUTER_API_KEY"]
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = "minimax/minimax-m2.7:free"

    def _mcp_tools_to_openai_format(self, mcp_tools):
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
        openai_tools = self._mcp_tools_to_openai_format(mcp_tools)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            temperature=0,
        )

        if response.choices is None:
          error_info = getattr(response, "error", {"message": "Unknown provider error"})
          raise RuntimeError(f"LLM provider error: {error_info}")

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