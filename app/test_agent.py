"""
Test the full agent loop with a single-tool question first.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.agent.agent import run_agent


async def main():
    question = "Find the top 5 Python AI repositories on GitHub and calculate their average star count."
    print(f"User: {question}\n")

    result = await run_agent(question)

    print("Tool calls made:")
    for call in result["tool_calls"]:
        print(f"  - {call['tool']}({call['arguments']}) -> {call['result']}")

    print(f"\nFinal answer: {result['answer']}")


if __name__ == "__main__":
    asyncio.run(main())