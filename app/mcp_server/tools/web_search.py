"""
Web search tool using Tavily (free tier: 1,000 searches/month, no card required).
Returns clean, LLM-friendly search results rather than raw HTML.
"""

import os
from tavily import TavilyClient


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for current information on a topic. Returns titles, URLs, and content snippets."""
    if max_results > 10:
        max_results = 10

    api_key = os.environ["TAVILY_API_KEY"]
    client = TavilyClient(api_key=api_key)

    response = client.search(query=query, max_results=max_results, search_depth="basic")

    results = []
    for item in response.get("results", []):
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
            }
        )
    return results