"""
Streamlit chat interface for the MCP AI Agent.
Shows the active model, available tools, and per-response tool usage.
"""

import asyncio
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.agent.agent import run_agent, SERVER_SCRIPT

st.set_page_config(page_title="MCP AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 MCP AI Agent")
st.caption("A universal AI agent powered by real MCP tool-calling.")


async def fetch_available_tools():
    """Connect to the MCP server briefly just to list its tools, for sidebar display."""
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])
    async with Client(stdio_client(server_params)) as client:
        result = await client.list_tools()
        return [t.name for t in result.tools]


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuration")

    provider = os.environ.get("LLM_PROVIDER", "groq")
    st.markdown(f"**Active LLM Provider:** `{provider}`")

    st.divider()
    st.subheader("🛠️ Available Tools")

    if "available_tools" not in st.session_state:
        with st.spinner("Loading tools..."):
            st.session_state.available_tools = asyncio.run(fetch_available_tools())

    for tool_name in st.session_state.available_tools:
        st.markdown(f"- `{tool_name}`")

    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# --- Chat state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages, including any tool calls made
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s) used"):
                for call in msg["tool_calls"]:
                    st.markdown(f"**`{call['tool']}`**")
                    st.code(f"Arguments: {call['arguments']}\nResult: {call['result']}")

# --- Handle new input ---
user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = asyncio.run(run_agent(user_input))
        st.markdown(result["answer"])

        if result["tool_calls"]:
            with st.expander(f"🔧 {len(result['tool_calls'])} tool call(s) used"):
                for call in result["tool_calls"]:
                    st.markdown(f"**`{call['tool']}`**")
                    st.code(f"Arguments: {call['arguments']}\nResult: {call['result']}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "tool_calls": result["tool_calls"],
        }
    )