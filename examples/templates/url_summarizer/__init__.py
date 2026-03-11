"""
URL Summarizer - Scrape any URL and return a structured summary.

Asks the user for a URL, scrapes the page, and produces a summary
covering the title, source, topic, key points, and takeaway.
"""

from .agent import UrlSummarizerAgent, default_agent, goal, nodes, edges
from .config import RuntimeConfig, AgentMetadata, default_config, metadata

__version__ = "1.0.0"

__all__ = [
    "UrlSummarizerAgent",
    "default_agent",
    "goal",
    "nodes",
    "edges",
    "RuntimeConfig",
    "AgentMetadata",
    "default_config",
    "metadata",
]
