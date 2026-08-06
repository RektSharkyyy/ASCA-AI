"""
Direct Agent - Handles conversational routes without heavy pipeline execution.

Two routes:
  1. `web_search` -> dispatches a structured query to the Tavily Web Search Tool,
     formats snippets/URLs into markdown, injects them into the system prompt as
     verified tool output, and synthesizes a grounded answer.
  2. `direct`     -> pure greetings / pleasantries / chitchat. Skips the search
     call entirely and generates a warm, contextual response immediately.

Designed for sub-second responses and minimal token consumption.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from src.infrastructure.config import config
from src.infrastructure.llm_loader import get_llm
from src.infrastructure.logging import logger
from src.agents.tools.web_search_tool import web_search_tool

RouteType = Literal["direct", "web_search"]

SYSTEM_PERSONA = (
    "You are ASCA AI, the Agricultural Supply Chain Advisory assistant for Sri Lankan "
    "farmers, economic centres (Dambulla, Thambuththegama) and B2B processing buyers. "
    "You are warm, concise and practical. Never invent prices, dates or figures."
)

DIRECT_INSTRUCTIONS = (
    "The user sent a greeting, pleasantry or light chitchat. Reply in ONE or TWO short, "
    "friendly sentences. Do not fabricate market data. If helpful, briefly mention that you "
    "can assist with crop price forecasts, surplus alerts, B2B buyer matching, invoices and "
    "financial reports. Mirror the user's language (English or Sinhala)."
)

WEB_SEARCH_INSTRUCTIONS = (
    "You have been given VERIFIED WEB SEARCH RESULTS below as tool output. Answer the user's "
    "question using ONLY those results. Be concise and factual. Quote figures exactly as they "
    "appear in the sources. Cite the source URLs inline as markdown links. If the results do not "
    "contain the answer, say so plainly instead of guessing."
)

NO_RESULTS_FALLBACK = (
    "I couldn't retrieve live web information for that right now. "
    "Please try again shortly, or ask me about crop prices, surplus alerts or B2B buyer "
    "matching using my internal market data."
)


class DirectAgentResponse(BaseModel):
    """Structured output returned by the Direct Agent."""

    route: RouteType = Field(..., description="Route taken: 'direct' or 'web_search'")
    answer: str = Field(..., description="Final natural-language answer for the user")
    search_performed: bool = Field(default=False, description="Whether the web search tool was called")
    search_query: Optional[str] = Field(default=None, description="Query dispatched to Tavily")
    sources: List[str] = Field(default_factory=list, description="Source URLs used to ground the answer")
    token_optimized: bool = Field(default=True, description="True when the pipeline skipped unnecessary calls")


class DirectAgent:
    """
    Lightweight conversational agent for `direct` and `web_search` routes.

    Encapsulates all search logic behind the isolated `web_search_tool` wrapper so the
    state machine (or LangGraph StateGraph) only needs to call `run()` / `run_async()`.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_search_results: int = 5,
    ):
        agent_cfg = (config.models.get("agent_models", {}) or {}).get("direct_agent", {}) or {}

        self.provider = provider or agent_cfg.get("provider") or config.env.DEFAULT_LLM_PROVIDER
        self.model_name = model_name or agent_cfg.get("llm_model") or "meta-llama/llama-3.1-8b-instruct"
        self.temperature = temperature
        self.max_search_results = max_search_results
        self._llm = None

    # ------------------------------------------------------------------ #
    # LLM plumbing
    # ------------------------------------------------------------------ #
    def _lazy_load_llm(self):
        """Loads the chat model only on first use to keep startup fast."""
        if self._llm is None:
            self._llm = get_llm(
                provider=self.provider,
                model_name=self.model_name,
                temperature=self.temperature,
            )
            logger.info(f"DirectAgent loaded LLM: {self.provider}/{self.model_name}")
        return self._llm

    def _invoke_llm(self, system_prompt: str, user_query: str) -> str:
        """Invokes the chat model, degrading gracefully on transient failures."""
        try:
            llm = self._lazy_load_llm()
            response = llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ]
            )
            return (getattr(response, "content", str(response)) or "").strip()
        except Exception as e:
            logger.error(f"DirectAgent LLM error: {e}")
            return ""

    # ------------------------------------------------------------------ #
    # Route: direct (greetings / chitchat) - no tool calls
    # ------------------------------------------------------------------ #
    def handle_direct(self, user_query: str) -> DirectAgentResponse:
        """Greetings and pleasantries: answers immediately, zero tool calls."""
        logger.info("DirectAgent route=direct (skipping web search entirely)")

        system_prompt = f"{SYSTEM_PERSONA}\n\n{DIRECT_INSTRUCTIONS}"
        answer = self._invoke_llm(system_prompt, user_query)

        if not answer:
            answer = (
                "Hello! I'm ASCA AI. I can help with crop price forecasts, surplus alerts, "
                "B2B buyer matching, invoices and financial reports. What would you like to know?"
            )

        return DirectAgentResponse(
            route="direct",
            answer=answer,
            search_performed=False,
            search_query=None,
            sources=[],
        )

    # ------------------------------------------------------------------ #
    # Route: web_search (real-time external info) - Tavily tool call
    # ------------------------------------------------------------------ #
    def _build_search_query(self, user_query: str) -> str:
        """Builds a structured, retrieval-friendly search query."""
        cleaned = " ".join((user_query or "").split())
        lowered = cleaned.lower()
        # Anchor to the local context when the user clearly means Sri Lanka domain topics.
        needs_local_anchor = any(
            kw in lowered for kw in ("exchange rate", "tax", "vat", "duty", "tariff", "fuel", "fertilizer", "import", "export")
        )
        if needs_local_anchor and "sri lanka" not in lowered:
            cleaned = f"{cleaned} Sri Lanka latest"
        return cleaned

    def handle_web_search(self, user_query: str) -> DirectAgentResponse:
        """Fetches live web results via Tavily and grounds the answer in them."""
        search_query = self._build_search_query(user_query)
        logger.info(f"DirectAgent route=web_search -> dispatching Tavily query: '{search_query}'")

        search_response = web_search_tool.search(
            query=search_query,
            max_results=self.max_search_results,
            include_answer=True,
            search_depth="basic",
        )

        sources = [r.url for r in search_response.results if r.url]

        if not search_response.results and not search_response.answer:
            logger.warning("DirectAgent: web search returned no usable payload.")
            return DirectAgentResponse(
                route="web_search",
                answer=NO_RESULTS_FALLBACK,
                search_performed=True,
                search_query=search_query,
                sources=[],
            )

        # Inject formatted tool output into the system prompt as verified context.
        tool_output_md = web_search_tool.format_results_as_markdown(search_response)
        system_prompt = (
            f"{SYSTEM_PERSONA}\n\n"
            f"{WEB_SEARCH_INSTRUCTIONS}\n\n"
            f"--- VERIFIED WEB SEARCH RESULTS (tool output) ---\n"
            f"{tool_output_md}\n"
            f"--- END OF TOOL OUTPUT ---"
        )

        answer = self._invoke_llm(system_prompt, user_query)

        if not answer:
            # Degrade to the raw Tavily summary rather than failing the turn.
            answer = search_response.answer or NO_RESULTS_FALLBACK
            if sources:
                answer += "\n\nSources:\n" + "\n".join(f"- {u}" for u in sources[:3])

        return DirectAgentResponse(
            route="web_search",
            answer=answer,
            search_performed=True,
            search_query=search_query,
            sources=sources,
        )

    # ------------------------------------------------------------------ #
    # Public entry points
    # ------------------------------------------------------------------ #
    def run(self, user_query: str, route: RouteType = "direct") -> DirectAgentResponse:
        """
        Main entry point used by the state machine / StateGraph node.

        Args:
            user_query: The raw user message.
            route: Upstream router verdict - 'web_search' or 'direct'.
        """
        if not user_query or not user_query.strip():
            return DirectAgentResponse(
                route="direct",
                answer="Could you please rephrase your question? I didn't receive any text.",
                search_performed=False,
            )

        if route == "web_search":
            return self.handle_web_search(user_query)
        return self.handle_direct(user_query)

    async def run_async(self, user_query: str, route: RouteType = "direct") -> DirectAgentResponse:
        """Async wrapper that keeps the event loop responsive during network I/O."""
        import asyncio

        return await asyncio.to_thread(self.run, user_query, route)

    # ------------------------------------------------------------------ #
    # LangGraph / state machine adapter
    # ------------------------------------------------------------------ #
    def as_graph_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        StateGraph-compatible node.

        Reads `query`/`user_query` and `route` from state, writes the agent output back.
        """
        user_query = state.get("query") or state.get("user_query") or ""
        route: RouteType = state.get("route", "direct")

        result = self.run(user_query, route)

        return {
            **state,
            "answer": result.answer,
            "route": result.route,
            "search_performed": result.search_performed,
            "search_query": result.search_query,
            "sources": result.sources,
        }


# Singleton instance
direct_agent = DirectAgent()
