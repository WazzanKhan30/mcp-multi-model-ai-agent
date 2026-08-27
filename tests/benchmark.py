"""
Simple performance benchmark for the agent.
Runs a few representative questions and reports timing/call-count metrics.
Not a pytest test - a standalone script to run manually and inspect.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.agent.agent import run_agent

BENCHMARK_QUESTIONS = [
    ("Simple calculator (1 tool)", "What is 25% of 8000?"),
    ("Weather lookup (1 tool, external API)", "What's the weather in Mumbai?"),
    ("Multi-step chaining (2 tools)", "What fantasy books do you have, and what's the average rating?"),
    ("GitHub + calculator (2 tools, external API)", "Find the top 3 Python AI repos on GitHub and calculate their average stars."),
]


async def run_benchmark():
    print(f"{'Question':<45} | {'Time (s)':>8} | {'Tool Calls':>10}")
    print("-" * 70)

    total_time = 0.0
    total_calls = 0

    for label, question in BENCHMARK_QUESTIONS:
        start = time.monotonic()
        result = await run_agent(question)
        elapsed = time.monotonic() - start

        total_time += elapsed
        total_calls += len(result["tool_calls"])

        print(f"{label:<45} | {elapsed:>8.2f} | {len(result['tool_calls']):>10}")

    print("-" * 70)
    print(f"{'TOTAL':<45} | {total_time:>8.2f} | {total_calls:>10}")
    print(f"{'AVERAGE per question':<45} | {total_time/len(BENCHMARK_QUESTIONS):>8.2f} |")


if __name__ == "__main__":
    asyncio.run(run_benchmark())