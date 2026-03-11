# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hive is an open-source AI Agent Framework by Aden (YC-backed) for building production-grade autonomous agents. The framework focuses on outcome-driven agent generation — developers describe goals, and the framework handles workflow construction, self-healing, and adaptation through failures.

## Commands

### Python / UV
```bash
# Run scripts and tests (always use uv, never python/python3 directly)
uv run <script>
uv pip install <package>

# Lint and format (Python)
make lint        # ruff check --fix + ruff format
make format      # ruff format only
make check       # verify without modifying (CI-safe)

# Tests
make test        # all unit tests (excludes live integration tests)
make test-tools  # tool tests with mocked APIs
make test-live   # integration tests (requires real API keys)
make test-all    # everything including live tests
```

### Frontend
```bash
make frontend-install  # npm install in core/frontend
make frontend-dev      # start Vite dev server
make frontend-build    # production build
```

### CLI (hive command)
```bash
hive run exports/my-agent --input '{"key": "value"}'
hive info exports/my-agent
hive validate exports/my-agent
hive list exports/
hive shell exports/my-agent

# Testing
hive test-run <agent_path> --goal <goal_id>
hive test-debug <agent_path> <test_name>
hive test-list <agent_path>
hive test-stats <agent_path>

hive open  # open dashboard in browser
```

## Architecture

### Repository Layout

The repo is a **UV workspace** with two Python packages:

- `core/` — Framework runtime, CLI, and web dashboard
  - `framework/` — Core Python package (`hive = framework.cli:main`)
    - `graph/` — Graph execution engine (nodes, edges, goal specs, parallel execution)
    - `llm/` — LLM provider abstraction (multi-provider via LiteLLM)
    - `runtime/` — Decision recording, run lifecycle, outcome tracking
    - `storage/` — Checkpoint store, file-based persistence
    - `monitoring/` — Cost and performance tracking
    - `observability/` — WebSocket tracing, structured logging
    - `testing/` — Goal-based test framework with fix suggestions
    - `runner/` — Agent execution and `AgentRunner`/`AgentOrchestrator`
    - `server/` — WebSocket + REST server for real-time monitoring
    - `agents/` — Built-in agent implementations
  - `frontend/` — React 18 + Vite + Tailwind dashboard
- `tools/` — 98+ MCP tools (FastMCP server at `tools/mcp_server.py`)
  - Tool categories: file system, web/search, communication (Gmail/Slack/Discord), CRM, cloud APIs (GCP/Stripe/GitHub), security, utilities
  - Credential management via `tools/src/aden_tools/credentials/`
- `examples/` — Agent templates and prompt-only recipes
- `docs/` — Architecture docs, key concepts, developer guides

### Key Abstractions

- **Graph** (`framework/graph/`) — Agents are directed graphs of nodes. Nodes implement the `Node` protocol. `GraphExecutor` handles parallel execution and retry logic. Edge conditions use safe Python eval.
- **Runtime** (`framework/runtime/`) — Records decisions (`Decision`, `Option`, `Outcome`). Every agent action is tracked for self-improvement.
- **LLMProvider** (`framework/llm/`) — Wraps LiteLLM; default model is `claude-haiku-4-5-20251001`. Supports 100+ models.
- **MCP Tools** — All tools are exposed via FastMCP server. Agents discover and invoke tools through the MCP protocol.
- **Testing** (`framework/testing/`) — Goal-based tests; tests are generated from goal definitions and can be run/debugged via `hive test-*` commands.

### Default LLM
`claude-haiku-4-5-20251001` (Anthropic). Supports OpenAI, Google, DeepSeek, and local models via Ollama.

## Code Style (ruff)

Ruff config lives in `core/pyproject.toml` under `[tool.ruff]`.

- Line length: 100 characters
- Python target: 3.11+
- Double quotes for strings
- `from __future__ import annotations` for modern type syntax
- Type hints required on all function signatures
- Import order: stdlib → third-party → first-party (`framework`) → local
- `raise X from e` in except blocks (B904)
- No unused imports (F401), no unused variables (F841)
- Prefer comprehensions over `map`/`filter`

`.claude/settings.json` runs `ruff check --fix` and `ruff format` automatically after every Edit/Write tool use.

## Agent and Multi-Agent Safety

- Do not create, apply, or drop `git stash` entries unless explicitly requested.
- Do not create, remove, or modify `git worktree` checkouts unless explicitly requested.
- Do not switch branches unless explicitly requested.
- When `push` is requested, you may `git pull --rebase` first, but never discard in-progress work.
- `commit` = commit only your changes; `commit all` = commit everything in grouped chunks.
- Ignore unrecognized files unrelated to your scoped changes.

## Change Hygiene

- Resolve formatting-only staged/unstaged diffs without asking.
- Include formatting-only follow-up changes in the same commit as the original request.
- Stop to confirm only when changes are semantic and may alter behavior.
- Do not update dependencies casually — version bumps require explicit approval.
- When working on a GitHub Issue or PR, print the full URL at the end of the task.
- Verify answers in code; do not guess.
