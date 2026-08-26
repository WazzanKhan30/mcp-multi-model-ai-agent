"""
Minimal Streamlit chat interface for the MCP AI Agent.
Phase 11, step 1: basic chat working end-to-end, no sidebar yet.
"""

import asyncio
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Make "app" package importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.agent.agent import run_agent

st.set_page_config(page_title="MCP AI Agent", page_icon="🤖")
st.title("🤖 MCP AI Agent")

# Persist chat history across Streamlit reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user input
user_input = st.chat_input("Ask me anything...")

if user_input:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run the agent and show the response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = asyncio.run(run_agent(user_input))
        st.markdown(result["answer"])

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})