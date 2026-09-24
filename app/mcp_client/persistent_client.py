"""
Persistent MCP client connection for the Streamlit app.

Spawning a new MCP server subprocess for every single chat message adds
latency and, on Windows, has been linked to Ctrl+C shutdown hangs when
many short-lived subprocess connections pile up. This module keeps ONE
long-lived connection open for the app's whole lifetime, running on a
dedicated background thread with its own asyncio event loop, and exposes
plain synchronous functions Streamlit's (sync) script can call directly.
"""

import asyncio
import atexit
import sys
import threading
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.agent.agent import run_agent

SERVER_SCRIPT = str(Path(__file__).resolve().parents[1] / "mcp_server" / "server.py")

_loop = None
_thread = None
_client = None
_client_cm = None
_loop_ready = threading.Event()
_lock = threading.Lock()


def _run_background_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop_ready.set()
    _loop.run_forever()


async def _connect():
    global _client, _client_cm
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])
    _client_cm = Client(stdio_client(server_params))
    _client = await _client_cm.__aenter__()


def _ensure_started():
    global _thread
    with _lock:
        if _thread is None:
            _thread = threading.Thread(target=_run_background_loop, daemon=True)
            _thread.start()
            _loop_ready.wait()
            future = asyncio.run_coroutine_threadsafe(_connect(), _loop)
            future.result()
            atexit.register(shutdown)


def shutdown():
    """Cleanly close the persistent MCP connection and stop the background loop."""
    global _client, _client_cm
    if _client_cm is not None and _loop is not None:
        try:
            future = asyncio.run_coroutine_threadsafe(
                _client_cm.__aexit__(None, None, None), _loop
            )
            future.result(timeout=5)
        except Exception:
            pass
        _loop.call_soon_threadsafe(_loop.stop)
    _client = None
    _client_cm = None


def run_agent_sync(user_message: str, username: str = "anonymous") -> dict:
    """Run one agent turn using the persistent MCP connection. Blocks until done."""
    _ensure_started()
    future = asyncio.run_coroutine_threadsafe(
        run_agent(user_message, mcp_client=_client, username=username), _loop
    )
    return future.result()


def list_tools_sync() -> list[str]:
    """List available tool names using the persistent MCP connection."""
    _ensure_started()

    async def _list():
        result = await _client.list_tools()
        return [t.name for t in result.tools]

    future = asyncio.run_coroutine_threadsafe(_list(), _loop)
    return future.result()