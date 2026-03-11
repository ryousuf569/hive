"""Node definitions for URL Summarizer."""

from framework.graph import NodeSpec

# Node 1: Intake (client-facing)
# Asks the user for the URL to summarize.
intake_node = NodeSpec(
    id="intake",
    name="Intake",
    description="Ask the user for the URL they want summarized.",
    node_type="event_loop",
    client_facing=True,
    input_keys=[],
    output_keys=["target_url"],
    system_prompt="""\
You are the intake assistant for a URL Summarizer agent.

**STEP 1 — Greet and ask:**
Greet the user briefly and ask them to provide the URL they want summarized.

After your greeting, call ask_user() to wait for their response.

**STEP 2 — After the user responds:**
Extract the URL from their message. If they provided a valid URL (starts with http:// or https://),
call:
  set_output("target_url", "<the URL they provided>")

If no valid URL was found, ask again with ask_user().
""",
    tools=[],
)

# Node 2: Summarize (autonomous, tool-using)
# Scrapes the URL and produces a structured text summary.
summarize_node = NodeSpec(
    id="summarize",
    name="Summarize",
    description="Scrape the URL and produce a structured summary.",
    node_type="event_loop",
    client_facing=False,
    input_keys=["target_url"],
    output_keys=["summary"],
    system_prompt="""\
You are the summarizer for a URL Summarizer agent.

Your task: scrape the page at target_url and produce a structured summary.

**Instructions:**
1. Call web_scrape(url=target_url, max_length=6000) to fetch the page content.
2. From the scraped content, extract:
   - **Title**: The page or article title.
   - **Source**: The domain name (e.g., "techcrunch.com").
   - **Topic**: One-line description of the subject matter.
   - **Key Points**: 3–5 bullet points covering the most important information.
   - **Takeaway**: A single sentence summarising the core message.
3. Format your output as plain text using the structure below.
4. Call set_output("summary", "<your formatted summary>").

**Output format:**
```
Title: <title>
Source: <domain>
Topic: <topic>

Key Points:
- <point 1>
- <point 2>
- <point 3>

Takeaway: <one sentence>
```

**Rules:**
- Only report what is actually on the page. Never fabricate content.
- If the scrape fails or returns no useful content, set_output("summary", "Could not retrieve content from <url>: <reason>").
- Keep key points concise (one sentence each).
""",
    tools=["web_scrape"],
)

__all__ = ["intake_node", "summarize_node"]
