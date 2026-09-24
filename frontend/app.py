"""
Streamlit chat interface for the MCP AI Agent.
Login/registration, per-user persistent sessions, rate limiting,
caching (server-side), metrics dashboard, and tool-usage visibility.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.mcp_client.persistent_client import run_agent_sync, list_tools_sync
from app.database import auth
from app.database import metrics as db_metrics
from app.database import queries as db_queries

st.set_page_config(page_title="MCP AI Agent", page_icon="🤖", layout="wide")

auth.init_users_table()
auth.init_chat_history_table()
auth.init_rate_limit_table()
db_metrics.init_metrics_table()
db_queries.init_documents_table()


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
    st.subheader("📄 Knowledge Base")
    with st.expander("➕ Add a document"):
        doc_title = st.text_input("Title", key="doc_title")
        doc_content = st.text_area("Content", key="doc_content", height=100)
        if st.button("Add Document"):
            if doc_title and doc_content:
                db_queries.add_document(st.session_state.username, doc_title, doc_content)
                st.success(f"Added '{doc_title}' to the knowledge base.")
            else:
                st.warning("Please provide both a title and content.")
    st.divider()
    st.subheader("🛠️ Available Tools")

    if "available_tools" not in st.session_state:
        with st.spinner("Loading tools..."):
            st.session_state.available_tools = list_tools_sync()

    for tool_name in st.session_state.available_tools:
        st.markdown(f"- `{tool_name}`")

    st.divider()
    st.subheader("📊 Metrics")
    stats = db_metrics.get_summary_stats()
    col1, col2 = st.columns(2)
    col1.metric("Total Requests", stats["total_requests"])
    col2.metric("Success Rate", f"{stats['success_rate']}%")
    col1.metric("Avg Response Time", f"{stats['avg_response_time']}s")
    col2.metric("Avg Tool Calls", stats["avg_tool_calls"])

    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        auth.clear_chat_history(st.session_state.username)
        st.rerun()

    if st.button("🚪 Log Out"):
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()


# --- Chat state: load persisted history on first load ---
if "messages" not in st.session_state:
    st.session_state.messages = auth.load_chat_history(st.session_state.username)

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
    allowed, rate_limit_message = auth.check_and_record_rate_limit(
        st.session_state.username, max_requests=15, window_minutes=5
    )

    if not allowed:
        st.error(rate_limit_message)
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
                        # Build simple history from the last few turns (role + content only,
            # excluding tool_calls metadata which the LLM API doesn't need)
            recent_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[-10:]  # last 10 messages, keeps context bounded
                if m["role"] in ("user", "assistant")
            ]
            result = run_agent_sync(
                user_input, username=st.session_state.username, history=recent_history
            )
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

    # Persist both messages to the database
    auth.save_message(st.session_state.username, "user", user_input)
    auth.save_message(
        st.session_state.username, "assistant", result["answer"], result["tool_calls"]
    )