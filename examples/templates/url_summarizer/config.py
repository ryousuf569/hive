"""Runtime configuration for URL Summarizer."""

from dataclasses import dataclass

from framework.config import RuntimeConfig

default_config = RuntimeConfig()


@dataclass
class AgentMetadata:
    name: str = "URL Summarizer"
    version: str = "1.0.0"
    description: str = (
        "Scrape any URL and produce a structured summary covering "
        "the main topic, key points, and a one-sentence takeaway."
    )
    intro_message: str = (
        "Hi! Paste a URL and I'll scrape it and return a clean summary."
    )


metadata = AgentMetadata()
