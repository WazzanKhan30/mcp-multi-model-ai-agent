"""
Streamlit chat interface for the MCP AI Agent.
Now with login/registration, per-user sessions, and tool-usage visibility.
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
from app.database import auth

st.set_page_config(page_title="MCP AI Agent", page_icon="🤖", layout="wide")

auth.init_users_table()


async def fetch_available_tools():
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])
    async with Client(stdio_client(server_params)) as client:
        result = await client.list_tools()
        return [t.name for t in result.tools]


# --- Authentication gate ---
if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.title("🤖 MCP AI Agent")
    st.caption("Please log in or create an account to continue.")

    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In"):
            if auth.verify_user(login_username, login_password):
                st.session_state.username = login_username
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab_register:
        reg_username = st.text_input("Choose a username", key="reg_username")
        reg_password = st.text_input("Choose a password", type="password", key="reg_password")
        if st.button("Register"):
            success, message = auth.register_user(reg_username, reg_password)
            if success:
                st.success(message + " You can now log in.")
            else:
                st.error(message)

    st.stop()  # don't render anything below until logged in


# --- Main app (only reached if logged in) ---
st.title("🤖 MCP AI Agent")
st.caption(f"Logged in as **{st.session_state.username}**")


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

    if st.button("🚪 Log Out"):
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s) used"):
                for call in msg["tool_calls"]:
                    st.markdown(f"**`{call['tool']}`**")
                    st.code(f"Arguments: {call['arguments']}\nResult: {call['result']}")

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