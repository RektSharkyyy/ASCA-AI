"""
Conversation Pipeline Orchestrator (state machine).

Execution order:
    1. Domain Guardrail  -> binary in_scope / out_of_scope (fail-open to in_scope)
                            out_of_scope short-circuits with OUT_OF_SCOPE_REPLY,
                            bypassing tools, RAG lookups and synthesis LLM calls.
    2. Query Router      -> direct | web_search | rag
    3. Terminal node     -> DirectAgent (direct / web_search) or the RAG/domain
                            pipeline handler injected by the caller.

The same wiring maps 1:1 onto a LangGraph StateGraph: each `*_node` method is a
node, and `route_after_guardrail` / `route_after_router` are conditional edges.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from src.infrastructure.logging import logger
from src.agents.intent_guardrail import (
    OUT_OF_SCOPE_REPLY,
    IntentClassification,
    domain_guardrail,
)
from src.agents.router import QueryRoute, query_router
from src.agents.direct_agent import direct_agent
from src.agents.rag_agent import market_rag_agent, MarketRAGAgent

# A RAG handler receives the user query (and optional centre_id) and returns a final answer string.
RagHandler = Callable[..., str]


class PipelineResult(BaseModel):
    """Final result of a single conversational turn."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Final answer shown to the user")
    in_scope: bool = Field(..., description="Guardrail verdict")
    route: Optional[str] = Field(default=None, description="Route taken when in scope")
    short_circuited: bool = Field(default=False, description="True when the guardrail blocked the pipeline")
    search_performed: bool = Field(default=False)
    sources: List[str] = Field(default_factory=list)
    guardrail_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    guardrail_reasoning: Optional[str] = Field(default=None)


class ConversationPipeline:
    """
    Orchestrates guardrail -> router -> agent for one user turn.

    Args:
        rag_handler: Optional callable that handles the `rag` route (heavy domain
            pipeline: market scout, matcher, report synthesizer). When omitted,
            defaults to `market_rag_agent.handle_query`.
    """

    def __init__(self, rag_handler: Optional[RagHandler] = None):
        self.guardrail = domain_guardrail
        self.router = query_router
        self.direct_agent = direct_agent
        self.rag_handler = rag_handler or market_rag_agent.handle_query

    # ------------------------------------------------------------------ #
    # Nodes
    # ------------------------------------------------------------------ #
    def guardrail_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 1: binary domain scope check. Runs before anything expensive."""
        query = state.get("query", "")
        verdict = self.guardrail.check_intent(query)
        in_scope = verdict.classification == IntentClassification.IN_SCOPE

        if not in_scope:
            logger.info("Guardrail verdict OUT_OF_SCOPE -> short-circuiting pipeline")

        return {
            **state,
            "in_scope": in_scope,
            "guardrail_confidence": verdict.confidence,
            "guardrail_reasoning": verdict.reasoning,
        }

    def refusal_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Terminal node for out-of-scope queries. Zero downstream LLM calls."""
        return {
            **state,
            "answer": OUT_OF_SCOPE_REPLY.strip(),
            "short_circuited": True,
            "route": None,
        }

    def router_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 2: picks the downstream route for in-scope queries."""
        decision = self.router.route(state.get("query", ""))
        return {
            **state,
            "route": decision.route.value,
            "route_confidence": decision.confidence,
            "route_reasoning": decision.reasoning,
        }

    def direct_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Terminal node for `direct` and `web_search` routes."""
        return self.direct_agent.as_graph_node(state)

    async def rag_node_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Terminal async node for the internal-data / domain pipeline route."""
        query = state.get("query", "")
        centre_id = state.get("centre_id", "DAMBULLA")

        if hasattr(market_rag_agent, "handle_query_async"):
            try:
                answer = await market_rag_agent.handle_query_async(query, default_centre=centre_id)
            except Exception as e:
                logger.error(f"Async RAG handler failed: {e}")
                answer = "I hit an error while analysing internal market data. Please try again."
        else:
            return self.rag_node(state)

        return {**state, "answer": answer, "search_performed": False, "sources": []}

    def rag_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Terminal node for the internal-data / domain pipeline route."""
        query = state.get("query", "")
        centre_id = state.get("centre_id", "DAMBULLA")

        if self.rag_handler is None:
            logger.warning("RAG route selected but no rag_handler is wired into the pipeline.")
            return {
                **state,
                "answer": (
                    "This question needs my internal market analytics pipeline, which isn't "
                    "connected in this configuration yet."
                ),
                "search_performed": False,
                "sources": [],
            }

        try:
            # Pass centre_id if supported by the handler, otherwise fallback to query only
            try:
                answer = self.rag_handler(query, default_centre=centre_id)
            except TypeError:
                answer = self.rag_handler(query)
        except Exception as e:
            logger.error(f"RAG handler failed: {e}")
            answer = "I hit an error while analysing internal market data. Please try again."

        return {**state, "answer": answer, "search_performed": False, "sources": []}

    # ------------------------------------------------------------------ #
    # Conditional edges
    # ------------------------------------------------------------------ #
    @staticmethod
    def route_after_guardrail(state: Dict[str, Any]) -> str:
        """Conditional edge: 'router' when in scope, 'refusal' otherwise."""
        return "router" if state.get("in_scope") else "refusal"

    @staticmethod
    def route_after_router(state: Dict[str, Any]) -> str:
        """Conditional edge: 'direct_agent' for direct/web_search, 'rag' otherwise."""
        route = state.get("route", QueryRoute.RAG.value)
        return "direct_agent" if route in (QueryRoute.DIRECT.value, QueryRoute.WEB_SEARCH.value) else "rag"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def run(self, query: str, centre_id: str = "DAMBULLA") -> PipelineResult:
        """Executes one full turn through the pipeline."""
        state: Dict[str, Any] = {"query": query, "centre_id": centre_id}

        state = self.guardrail_node(state)

        if self.route_after_guardrail(state) == "refusal":
            state = self.refusal_node(state)
            return self._to_result(state)

        state = self.router_node(state)

        if self.route_after_router(state) == "direct_agent":
            state = self.direct_agent_node(state)
        else:
            state = self.rag_node(state)

        return self._to_result(state)

    async def run_async(self, query: str, centre_id: str = "DAMBULLA") -> PipelineResult:
        """Async execution turn through the pipeline."""
        state: Dict[str, Any] = {"query": query, "centre_id": centre_id}

        state = self.guardrail_node(state)

        if self.route_after_guardrail(state) == "refusal":
            state = self.refusal_node(state)
            return self._to_result(state)

        state = self.router_node(state)

        if self.route_after_router(state) == "direct_agent":
            state = await asyncio.to_thread(self.direct_agent_node, state)
        else:
            state = await self.rag_node_async(state)

        return self._to_result(state)

    @staticmethod
    def _to_result(state: Dict[str, Any]) -> PipelineResult:
        return PipelineResult(
            query=state.get("query", ""),
            answer=state.get("answer", ""),
            in_scope=bool(state.get("in_scope", False)),
            route=state.get("route"),
            short_circuited=bool(state.get("short_circuited", False)),
            search_performed=bool(state.get("search_performed", False)),
            sources=state.get("sources", []) or [],
            guardrail_confidence=state.get("guardrail_confidence", 1.0),
            guardrail_reasoning=state.get("guardrail_reasoning"),
        )

    # ------------------------------------------------------------------ #
    # Optional LangGraph compilation
    # ------------------------------------------------------------------ #
    def build_langgraph(self):
        """
        Compiles the same wiring into a LangGraph StateGraph.

        Requires `langgraph` to be installed; raises ImportError otherwise so the
        plain state machine above remains usable without the extra dependency.
        """
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(dict)

        graph.add_node("guardrail", self.guardrail_node)
        graph.add_node("refusal", self.refusal_node)
        graph.add_node("router", self.router_node)
        graph.add_node("direct_agent", self.direct_agent_node)
        graph.add_node("rag", self.rag_node)

        graph.add_edge(START, "guardrail")
        graph.add_conditional_edges(
            "guardrail",
            self.route_after_guardrail,
            {"router": "router", "refusal": "refusal"},
        )
        graph.add_conditional_edges(
            "router",
            self.route_after_router,
            {"direct_agent": "direct_agent", "rag": "rag"},
        )
        graph.add_edge("refusal", END)
        graph.add_edge("direct_agent", END)
        graph.add_edge("rag", END)

        return graph.compile()


# Singleton instance (wire a rag_handler in when the domain pipeline is ready)
conversation_pipeline = ConversationPipeline()
