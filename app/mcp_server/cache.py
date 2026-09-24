"""
Simple in-memory TTL (time-to-live) cache for tool results.
Avoids redundant external API calls when the same tool is called
with the same arguments within a short time window.
"""

import time
import json
import hashlib
from app.logger import get_logger

logger = get_logger("cache")

_cache: dict[str, tuple[float, any]] = {}

DEFAULT_TTL_SECONDS = 120  # how long a cached result stays valid


def _make_key(tool_name: str, arguments: dict) -> str:
    """Build a stable cache key from a tool name + its arguments."""
    args_str = json.dumps(arguments, sort_keys=True)
    raw = f"{tool_name}:{args_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_cached(tool_name: str, arguments: dict):
    """Return the cached result if present and not expired, else None."""
    key = _make_key(tool_name, arguments)
    entry = _cache.get(key)
    if entry is None:
        return None

    cached_at, value = entry
    if time.time() - cached_at > DEFAULT_TTL_SECONDS:
        del _cache[key]  # expired, evict it
        return None

    logger.info(f"Cache HIT | tool={tool_name} | args={arguments}")
    return value


def set_cached(tool_name: str, arguments: dict, value):
    """Store a tool result in the cache."""
    key = _make_key(tool_name, arguments)
    _cache[key] = (time.time(), value)
    logger.info(f"Cache SET | tool={tool_name} | args={arguments}")


def cache_stats() -> dict:
    """Return basic stats about the current cache state (useful for the metrics work later)."""
    now = time.time()
    active = sum(1 for cached_at, _ in _cache.values() if now - cached_at <= DEFAULT_TTL_SECONDS)
    return {"total_entries": len(_cache), "active_entries": active}