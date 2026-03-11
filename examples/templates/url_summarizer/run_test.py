"""
Non-interactive test runner for URL Summarizer.

Bypasses the client-facing intake node and starts directly at the
summarize node, pre-loading a fixed URL into SharedMemory via input_data.

Usage:
    cd <repo-root>
    uv run python -m examples.templates.url_summarizer.run_test
"""

from __future__ import annotations

import asyncio
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve repo root so the script works from any cwd
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # hive/
CORE_DIR = REPO_ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------
TEST_URL = "https://en.wikipedia.org/wiki/Python_(programming_language)"
OUTPUT_FILE = Path(__file__).parent / "agent_test_output.md"


# ---------------------------------------------------------------------------
# Agent bootstrap (entry at "summarize", input_data pre-loads target_url)
# ---------------------------------------------------------------------------
async def run_test():
    from framework.graph.edge import GraphSpec
    from framework.graph.executor import GraphExecutor
    from framework.llm import LiteLLMProvider
    from framework.runtime.core import Runtime
    from framework.runtime.event_bus import EventBus
    from framework.runner.tool_registry import ToolRegistry

    from examples.templates.url_summarizer.agent import goal, summarize_node
    from examples.templates.url_summarizer.config import default_config

    storage_path = Path.home() / ".hive" / "url_summarizer_test"
    storage_path.mkdir(parents=True, exist_ok=True)

    event_bus = EventBus()
    tool_registry = ToolRegistry()

    mcp_config = Path(__file__).parent / "mcp_servers.json"
    if mcp_config.exists():
        tool_registry.load_mcp_config(mcp_config)

    llm = LiteLLMProvider(
        model=default_config.model,
        api_key=default_config.api_key,
        api_base=default_config.api_base,
    )

    tools = list(tool_registry.get_tools().values())
    tool_executor = tool_registry.get_executor()

    # Single-node graph starting (and ending) at "summarize"
    graph = GraphSpec(
        id="url-summarizer-test-graph",
        goal_id=goal.id,
        version="1.0.0",
        entry_node="summarize",
        entry_points={"direct": "summarize"},
        terminal_nodes=["summarize"],
        pause_nodes=[],
        nodes=[summarize_node],
        edges=[],
        default_model=default_config.model,
        max_tokens=default_config.max_tokens,
        loop_config={
            "max_iterations": 20,
            "max_tool_calls_per_turn": 10,
            "max_history_tokens": 16000,
        },
    )

    runtime = Runtime(storage_path)
    executor = GraphExecutor(
        runtime=runtime,
        llm=llm,
        tools=tools,
        tool_executor=tool_executor,
        event_bus=event_bus,
        storage_path=storage_path,
        loop_config=graph.loop_config,
    )

    print(f"Running summarize node on: {TEST_URL}", flush=True)
    result = await executor.execute(
        graph=graph,
        goal=goal,
        input_data={"target_url": TEST_URL},
        validate_graph=False,  # single-node graphs have no edges
    )
    return result


# ---------------------------------------------------------------------------
# Write output to agent_test_output.md
# ---------------------------------------------------------------------------
def write_output(result, elapsed_s: float) -> None:
    run_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if result.success:
        summary_text = result.output.get("summary", "(no summary key in output)")
    else:
        summary_text = f"ERROR: {result.error}"

    content = textwrap.dedent(f"""\
        # URL Summarizer — Test Run

        **Date:** {run_at}
        **Command:**
        ```bash
        uv run python -m examples.templates.url_summarizer.run_test
        ```

        ---

        ## Input

        | Field | Value |
        |---|---|
        | URL | `{TEST_URL}` |
        | Entry node | `summarize` (intake bypassed) |
        | Model | configured via `~/.hive/configuration.json` |

        ---

        ## Output

        ```
        {summary_text}
        ```

        ---

        ## Execution Metrics

        | Metric | Value |
        |---|---|
        | Success | `{result.success}` |
        | Steps executed | `{result.steps_executed}` |
        | Path | `{" → ".join(result.path) if result.path else "summarize"}` |
        | Wall time | `{elapsed_s:.1f}s` |
        | Execution quality | `{result.execution_quality}` |
    """)

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"\nOutput written to: {OUTPUT_FILE}", flush=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time

    t0 = time.monotonic()
    try:
        result = asyncio.run(run_test())
    except Exception as exc:
        elapsed = time.monotonic() - t0
        # Still write a failure report so the file always exists
        from framework.graph.executor import ExecutionResult

        result = ExecutionResult(success=False, error=str(exc))
        result.execution_quality = "failed"
        write_output(result, elapsed)
        print(f"Test failed: {exc}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.monotonic() - t0
    write_output(result, elapsed)
    sys.exit(0 if result.success else 1)
