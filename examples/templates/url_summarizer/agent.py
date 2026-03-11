"""Agent graph construction for URL Summarizer."""

from framework.graph import EdgeSpec, EdgeCondition, Goal, SuccessCriterion, Constraint
from framework.graph.edge import GraphSpec
from framework.graph.executor import ExecutionResult, GraphExecutor
from framework.runtime.event_bus import EventBus
from framework.runtime.core import Runtime
from framework.llm import LiteLLMProvider
from framework.runner.tool_registry import ToolRegistry

from .config import default_config, metadata
from .nodes import intake_node, summarize_node

# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------

goal = Goal(
    id="url-summarizer",
    name="URL Summarizer",
    description=(
        "Scrape any URL provided by the user and produce a structured summary "
        "covering the title, source, topic, key points, and a one-sentence takeaway."
    ),
    success_criteria=[
        SuccessCriterion(
            id="sc-page-scraped",
            description="The page content was successfully retrieved",
            metric="page_scraped",
            target="true",
            weight=0.4,
        ),
        SuccessCriterion(
            id="sc-summary-structured",
            description="Summary includes title, key points, and takeaway",
            metric="summary_structured",
            target="true",
            weight=0.4,
        ),
        SuccessCriterion(
            id="sc-summary-delivered",
            description="Summary is returned to the user",
            metric="summary_delivered",
            target="true",
            weight=0.2,
        ),
    ],
    constraints=[
        Constraint(
            id="c-no-fabrication",
            description="Only report content actually found on the page",
            constraint_type="hard",
            category="quality",
        ),
    ],
)

# ---------------------------------------------------------------------------
# Graph topology
# ---------------------------------------------------------------------------

nodes = [intake_node, summarize_node]

edges = [
    EdgeSpec(
        id="intake-to-summarize",
        source="intake",
        target="summarize",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
]

entry_node = "intake"
entry_points = {"start": "intake"}
pause_nodes: list[str] = []
terminal_nodes = ["summarize"]


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class UrlSummarizerAgent:
    """
    URL Summarizer — 2-node pipeline.

    Flow: intake -> summarize
    """

    def __init__(self, config=None):
        self.config = config or default_config
        self.goal = goal
        self.nodes = nodes
        self.edges = edges
        self.entry_node = entry_node
        self.entry_points = entry_points
        self.pause_nodes = pause_nodes
        self.terminal_nodes = terminal_nodes
        self._executor: GraphExecutor | None = None
        self._graph: GraphSpec | None = None
        self._event_bus: EventBus | None = None
        self._tool_registry: ToolRegistry | None = None

    def _build_graph(self) -> GraphSpec:
        """Build the GraphSpec."""
        return GraphSpec(
            id="url-summarizer-graph",
            goal_id=self.goal.id,
            version="1.0.0",
            entry_node=self.entry_node,
            entry_points=self.entry_points,
            terminal_nodes=self.terminal_nodes,
            pause_nodes=self.pause_nodes,
            nodes=self.nodes,
            edges=self.edges,
            default_model=self.config.model,
            max_tokens=self.config.max_tokens,
            loop_config={
                "max_iterations": 20,
                "max_tool_calls_per_turn": 10,
                "max_history_tokens": 16000,
            },
        )

    def _setup(self) -> GraphExecutor:
        """Set up the executor with all components."""
        from pathlib import Path

        storage_path = Path.home() / ".hive" / "url_summarizer"
        storage_path.mkdir(parents=True, exist_ok=True)

        self._event_bus = EventBus()
        self._tool_registry = ToolRegistry()

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            self._tool_registry.load_mcp_config(mcp_config_path)

        llm = LiteLLMProvider(
            model=self.config.model,
            api_key=self.config.api_key,
            api_base=self.config.api_base,
        )

        tool_executor = self._tool_registry.get_executor()
        tools = list(self._tool_registry.get_tools().values())

        self._graph = self._build_graph()
        runtime = Runtime(storage_path)

        self._executor = GraphExecutor(
            runtime=runtime,
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
            event_bus=self._event_bus,
            storage_path=storage_path,
            loop_config=self._graph.loop_config,
        )

        return self._executor

    async def start(self) -> None:
        """Set up the agent (initialize executor and tools)."""
        if self._executor is None:
            self._setup()

    async def stop(self) -> None:
        """Clean up resources."""
        self._executor = None
        self._event_bus = None

    async def trigger_and_wait(
        self,
        entry_point: str,
        input_data: dict,
        timeout: float | None = None,
        session_state: dict | None = None,
    ) -> ExecutionResult | None:
        """Execute the graph and wait for completion."""
        if self._executor is None:
            raise RuntimeError("Agent not started. Call start() first.")
        if self._graph is None:
            raise RuntimeError("Graph not built. Call start() first.")

        return await self._executor.execute(
            graph=self._graph,
            goal=self.goal,
            input_data=input_data,
            session_state=session_state,
        )

    async def run(self, context: dict, session_state=None) -> ExecutionResult:
        """Run the agent (convenience method for single execution)."""
        await self.start()
        try:
            result = await self.trigger_and_wait(
                "start", context, session_state=session_state
            )
            return result or ExecutionResult(success=False, error="Execution timeout")
        finally:
            await self.stop()

    def info(self):
        """Get agent information."""
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "goal": {
                "name": self.goal.name,
                "description": self.goal.description,
            },
            "nodes": [n.id for n in self.nodes],
            "edges": [e.id for e in self.edges],
            "entry_node": self.entry_node,
            "entry_points": self.entry_points,
            "pause_nodes": self.pause_nodes,
            "terminal_nodes": self.terminal_nodes,
            "client_facing_nodes": [n.id for n in self.nodes if n.client_facing],
        }

    def validate(self):
        """Validate agent structure."""
        errors = []
        warnings = []

        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge {edge.id}: source '{edge.source}' not found")
            if edge.target not in node_ids:
                errors.append(f"Edge {edge.id}: target '{edge.target}' not found")

        if self.entry_node not in node_ids:
            errors.append(f"Entry node '{self.entry_node}' not found")

        for terminal in self.terminal_nodes:
            if terminal not in node_ids:
                errors.append(f"Terminal node '{terminal}' not found")

        for ep_id, node_id in self.entry_points.items():
            if node_id not in node_ids:
                errors.append(
                    f"Entry point '{ep_id}' references unknown node '{node_id}'"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Conventional entry point used by `hive run` and the dashboard
default_agent = UrlSummarizerAgent()
