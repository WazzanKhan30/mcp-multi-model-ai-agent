"""
End-to-end test of the full agent loop: real LLM + real MCP tools.
This is the core demonstration of the entire project - genuine
multi-step tool chaining, no mocking.

Note: requires a valid GROQ_API_KEY in .env, and makes real API calls.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.agent.agent import run_agent


@pytest.mark.asyncio
async def test_simple_calculator_question():
    result = await run_agent("What is 25% of 8000?")
    assert len(result["tool_calls"]) >= 1

    # Normalize the answer (strip commas, since the LLM may format
    # numbers as "2,000" instead of "2000" - both are correct)
    normalized_answer = result["answer"].replace(",", "")
    assert "2000" in normalized_answer


@pytest.mark.asyncio
async def test_multi_step_database_and_calculator_chaining():
    result = await run_agent(
        "What fantasy books do you have, and what's the average rating of them?"
    )
    tool_names_used = [call["tool"] for call in result["tool_calls"]]
    assert "search_books_by_genre" in tool_names_used
    assert "average" in tool_names_used
    assert len(result["tool_calls"]) >= 2


@pytest.mark.asyncio
async def test_agent_handles_tool_error_gracefully():
    result = await run_agent(
        "Use your divide tool to calculate 10 divided by 0. You must use the tool."
    )
    # Should complete without crashing, and mention the impossibility in the answer
    assert result["answer"] is not None
    assert len(result["answer"]) > 0
    