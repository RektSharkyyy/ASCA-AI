"""
Query Router - Upstream classifier that decides which downstream path handles a query.

Routes:
  - `direct`      : greetings, pleasantries, chitchat  -> DirectAgent (no tools)
  - `web_search`  : real-time external info (live FX rates, current tax updates,
                    weather advisories, global commodity news) -> DirectAgent + Tavily
  - `rag`         : internal knowledge / domain pipeline (market scout, matcher,
                    invoices, clients, financial reports)

Uses a cheap deterministic heuristic first, then falls back to a lightweight LLM.
Fails open to `rag` so domain questions are never lost.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.infrastructure.config import config
from src.infrastructure.llm_loader import get_llm
from src.infrastructure.logging import logger


class QueryRoute(str, Enum):
    DIRECT = "direct"
    WEB_SEARCH = "web_search"
    RAG = "rag"


class RouteDecision(BaseModel):
    """Structured routing verdict."""

    route: QueryRoute = Field(..., description="Chosen downstream route")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = Field(default=None)


# Short, unambiguous conversational openers -> `direct`
_GREETING_TOKENS = {
    "hi", "hii", "hey", "hello", "helo", "yo", "hiya",
    "thanks", "thank you", "thankyou", "ty", "cheers",
    "bye", "goodbye", "good bye", "see you",
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how r u", "whats up", "what's up", "sup",
    "ok", "okay", "cool", "nice", "great", "awesome",
    # Sinhala transliterations commonly typed by users
    "ayubowan", "stuti", "istuti", "hari", "hondai",
}

# Signals that the answer requires fresh, external, non-database information
_WEB_SEARCH_TOKENS = {
    "exchange rate", "usd", "dollar rate", "forex", "currency",
    "tax update", "vat rate", "new tax", "budget", "gazette", "government policy",
    "latest news", "current news", "today's news", "breaking",
    "weather forecast", "monsoon", "rainfall forecast", "drought warning",
    "global price", "world market", "international price", "export price",
    "fuel price", "fertilizer price", "diesel price", "petrol price",
    "right now", "as of today", "this week", "recent update", "live",
}

# Signals that internal data / the heavy domain pipeline is required
_RAG_TOKENS = {
    "invoice", "client", "financial report", "revenue", "payment", "ledger",
    "dambulla", "thambuththegama", "economic center", "economic centre",
    "surplus", "forecast", "predict", "b2b", "buyer", "matcher", "fefo",
    "wholesale price", "supply volume", "advisory", "blueprint", "anomaly",
}


class QueryRouter:
    """
    Classifies an in-scope query into `direct`, `web_search`, or `rag`.

    Runs immediately after the Domain Guardrail. Heuristics resolve the common
    cases in microseconds; the LLM is only consulted for genuinely ambiguous input.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        fail_open_route: QueryRoute = QueryRoute.RAG,
    ):
        router_cfg = (config.models.get("agent_models", {}) or {}).get("query_router", {}) or {}
        self.provider = provider or router_cfg.get("provider") or config.env.DEFAULT_LLM_PROVIDER
        self.model_name = model_name or router_cfg.get("llm_model") or "meta-llama/llama-3.1-8b-instruct"
        self.fail_open_route = fail_open_route
        self._llm = None

    # ------------------------------------------------------------------ #
    # Heuristic fast path
    # ------------------------------------------------------------------ #
    def _heuristic_route(self, query: str) -> Optional[RouteDecision]:
        """Resolves obvious cases without any network call."""
        text = " ".join((query or "").lower().split())
        stripped = text.strip(" .!?,")

        # 1. Very short pure greeting / pleasantry
        if stripped in _GREETING_TOKENS:
            return RouteDecision(route=QueryRoute.DIRECT, confidence=0.98, reasoning="Exact greeting match")

        word_count = len(stripped.split())
        if word_count <= 4 and any(stripped.startswith(tok) for tok in _GREETING_TOKENS):
            return RouteDecision(route=QueryRoute.DIRECT, confidence=0.9, reasoning="Short greeting phrase")

        rag_hits = sum(1 for tok in _RAG_TOKENS if tok in text)
        web_hits = sum(1 for tok in _WEB_SEARCH_TOKENS if tok in text)

        # 2. Clear real-time external information request
        if web_hits > 0 and web_hits >= rag_hits:
            return RouteDecision(
                route=QueryRoute.WEB_SEARCH,
                confidence=0.9,
                reasoning=f"Matched {web_hits} real-time information signal(s)",
            )

        # 3. Clear internal-data request
        if rag_hits > 0:
            return RouteDecision(
                route=QueryRoute.RAG,
                confidence=0.9,
                reasoning=f"Matched {rag_hits} internal-domain signal(s)",
            )

        return None

    # ------------------------------------------------------------------ #
    # LLM fallback
    # ------------------------------------------------------------------ #
    def _lazy_load_llm(self):
        if self._llm is None:
            self._llm = get_llm(provider=self.provider, model_name=self.model_name, temperature=0.0)
            logger.info(f"QueryRouter loaded LLM: {self.provider}/{self.model_name}")
        return self._llm

    def _llm_route(self, query: str) -> RouteDecision:
        """Consults the lightweight model for ambiguous queries; fails open to RAG."""
        system_prompt = """You are a query router for ASCA AI, an Agricultural Supply Chain Advisory system for Sri Lanka.

Choose EXACTLY ONE route:
- "direct": greetings, thanks, small talk, pleasantries. No data needed.
- "web_search": needs CURRENT external information not in our database
  (live exchange rates, new tax/government updates, weather forecasts,
   global commodity news, fuel/fertilizer prices).
- "rag": needs our INTERNAL data or analytics
  (crop price forecasts, surplus anomalies, B2B buyer matching,
   invoices, clients, financial reports, economic centre analytics).

Respond ONLY with JSON:
{"route": "direct" | "web_search" | "rag", "confidence": 0.0-1.0, "reasoning": "one short sentence"}"""

        try:
            llm = self._lazy_load_llm()
            response = llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Route this query:\n\n{query}"},
                ]
            )
            raw = (getattr(response, "content", str(response)) or "").strip()

            import json

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)
            decision = RouteDecision(**data)
            logger.info(f"QueryRouter LLM verdict: {decision.route.value} ({decision.confidence:.2f})")
            return decision

        except Exception as e:
            logger.error(f"QueryRouter LLM error: {e} -> failing open to '{self.fail_open_route.value}'")
            return RouteDecision(
                route=self.fail_open_route,
                confidence=0.5,
                reasoning=f"Router error, defaulted to {self.fail_open_route.value} (fail-open)",
            )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def route(self, query: str) -> RouteDecision:
        """Returns the routing verdict for an in-scope query."""
        if not query or not query.strip():
            return RouteDecision(route=QueryRoute.DIRECT, confidence=1.0, reasoning="Empty query")

        fast = self._heuristic_route(query)
        if fast is not None:
            logger.info(f"QueryRouter heuristic verdict: {fast.route.value} ({fast.reasoning})")
            return fast

        return self._llm_route(query)

    async def route_async(self, query: str) -> RouteDecision:
        import asyncio

        return await asyncio.to_thread(self.route, query)


# Singleton instance
query_router = QueryRouter()
