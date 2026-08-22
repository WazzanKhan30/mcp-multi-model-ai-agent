"""
Thin wrapper around the Gemini API for our agent.
Converts MCP tool schemas into the format Gemini's function-calling expects,
and translates Gemini's responses into a simple, provider-agnostic shape.
"""

import os
from google import genai
from google.genai import types


class GeminiProvider:
    def __init__(self):
        api_key = os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.6-flash"

    def _mcp_tools_to_gemini_format(self, mcp_tools):
        """Convert MCP tool definitions into Gemini FunctionDeclaration objects."""
        declarations = []
        for tool in mcp_tools:
            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=tool.input_schema,
                )
            )
        return types.Tool(function_declarations=declarations)

    def generate(self, user_message: str, mcp_tools: list):
        """
        Send a message to Gemini along with available MCP tools.
        Returns either a text response or a requested tool call.
        """
        gemini_tools = [self._mcp_tools_to_gemini_format(mcp_tools)]

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                tools=gemini_tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True  # WE control tool execution via MCP, not the SDK
                ),
            ),
        )

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if part.function_call:
            return {
                "type": "tool_call",
                "name": part.function_call.name,
                "arguments": dict(part.function_call.args),
            }
        else:
            return {"type": "text", "text": response.text}