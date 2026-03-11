        # URL Summarizer — Test Run

        **Date:** 2026-03-11 11:23:30 UTC
        **Command:**
        ```bash
        # Standalone (no framework install needed):
        python examples/templates/url_summarizer/standalone_test.py

        # Full framework run (after ./quickstart.sh):
        uv run python -m examples.templates.url_summarizer.run_test
        ```

        ---

        ## Input

        | Field | Value |
        |---|---|
        | URL | `https://docs.python.org/3/library/asyncio.html` |
        | Entry node | `summarize` (intake bypassed for test) |
        | Scrape max length | `6000 chars` |

        ---

        ## Scrape Step (web_scrape tool)

        **Title:** asyncio — Asynchronous I/O — Python 3.14.3 documentation
        **Domain:** docs.python.org
        **Content preview (first 400 chars of 3342 scraped):**

        ```
        asyncio — Asynchronous I/O — Python 3.14.3 documentation
Navigation
index
modules
|
next
|
previous
|
Python
»
3.14.3 Documentation
»
The Python Standard Library
»
Networking and Interprocess Communication
»
asyncio
— Asynchronous I/O
|
Theme
Auto
Light
Dark
|
asyncio
— Asynchronous I/O
¶
asyncio is a library to write
concurrent
code using
the
async/await
syntax.
asyncio is used as a foundation fo…
        ```

        ---

        ## Agent Output (summarize_node)

        ```
        Title: asyncio — Asynchronous I/O — Python 3.14.3 documentation
Source: docs.python.org
Topic: asyncio — Asynchronous I/O — Python 3.14.3 documentation

Key Points:
- asyncio is used as a foundation for multiple Python asynchronous
- frameworks that provide high-performance network and web-servers,
- database connection libraries, distributed task queues, etc.
- This module does not work or is not available on WebAssembly. See
- Type "help", "copyright", "credits" or "license" for more information.

Takeaway: asyncio is used as a foundation for multiple Python asynchronous
        ```

        ---

        ## Execution Metrics

        | Metric | Value |
        |---|---|
        | Success | `True` |
        | Scrape length | `3342 chars` |
        | Wall time | `0.80s` |
        | Error | `none` |

        ---

        ## Framework Notes

        This test was executed without the Hive framework (no `.venv`,
        no `uv`, no LLM call) because `quickstart.sh` has not been run.

        In a full framework run:
        - `web_scrape` is provided by the Hive MCP tools server (`tools/mcp_server.py`)
        - The LLM (configured in `~/.hive/configuration.json`) generates the
          summary from the scraped content using the `summarize_node` system prompt
        - `set_output("summary", ...)` stores the result in SharedMemory
        - `GraphExecutor` records a `Decision` to the `Runtime` for observability

        To run the full agent:
        ```bash
        # 1. Install uv
        curl -Ls https://astral.sh/uv/install.sh | sh

        # 2. Set up the framework
        ./quickstart.sh

        # 3. Run the test
        uv run python -m examples.templates.url_summarizer.run_test
        ```
