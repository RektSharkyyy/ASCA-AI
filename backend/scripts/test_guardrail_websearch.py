"""
Smoke test for the Guardrail + Direct Web Search architecture.

Verifies:
  1. Out-of-scope queries short-circuit with OUT_OF_SCOPE_REPLY (no tools, no RAG).
  2. In-scope greetings take the `direct` route with ZERO search calls.
  3. Real-time queries take the `web_search` route and hit the Tavily tool.
  4. Domain queries take the `rag` route.
  5. The guardrail FAILS OPEN to in_scope when the LLM raises a network error.

Run:  python scripts/test_guardrail_websearch.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.logging import logger
from src.agents.intent_guardrail import (
    IntentClassification,
    OUT_OF_SCOPE_REPLY,
    DomainGuardrail,
    domain_guardrail,
)
from src.agents.router import QueryRoute, query_router
from src.agents.tools.web_search_tool import (
    SearchResult,
    WebSearchResponse,
    web_search_tool,
)
from src.agents.pipeline import ConversationPipeline


PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((name, status))
    logger.info(f"[{status}] {name}{(' -> ' + detail) if detail else ''}")


# --------------------------------------------------------------------------- #
# 1. Guardrail classification (keyword fast-path, no network required)
# --------------------------------------------------------------------------- #
def test_guardrail_classification():
    logger.info("=== Test 1: Domain Guardrail classification (keyword fast-path) ===")

    out_of_scope_query = "Write me a python script to debug javascript programming errors"
    verdict = domain_guardrail.check_intent(out_of_scope_query)
    check(
        "Out-of-scope query classified OUT_OF_SCOPE",
        verdict.classification == IntentClassification.OUT_OF_SCOPE,
        verdict.classification.value,
    )

    in_scope_query = "What is the wholesale tomato price forecast for the Dambulla market?"
    verdict = domain_guardrail.check_intent(in_scope_query)
    check(
        "Domain query classified IN_SCOPE",
        verdict.classification == IntentClassification.IN_SCOPE,
        verdict.classification.value,
    )

    verdict = domain_guardrail.check_intent("hello")
    check(
        "Greeting classified IN_SCOPE (served by direct route)",
        verdict.classification == IntentClassification.IN_SCOPE,
        verdict.classification.value,
    )


# --------------------------------------------------------------------------- #
# 2. Fail-open strategy on transient LLM failure
# --------------------------------------------------------------------------- #
def test_guardrail_fail_open():
    logger.info("=== Test 2: Fail-open strategy on LLM network failure ===")

    class BoomLLM:
        def invoke(self, *_args, **_kwargs):
            raise ConnectionError("Simulated transient network failure")

    guard = DomainGuardrail(fail_open=True)
    guard.llm = BoomLLM()  # bypass lazy loading with a failing client

    # Ambiguous query -> no keyword shortcut -> forced down the LLM path
    verdict = guard._classify_with_llm("Tell me something interesting about that thing")
    check(
        "LLM failure defaults to IN_SCOPE (fail-open)",
        verdict.classification == IntentClassification.IN_SCOPE,
        verdict.reasoning or "",
    )

    guard_closed = DomainGuardrail(fail_open=False)
    guard_closed.llm = BoomLLM()
    verdict = guard_closed._classify_with_llm("Tell me something interesting about that thing")
    check(
        "fail_open=False rejects on LLM failure (fail-closed)",
        verdict.classification == IntentClassification.OUT_OF_SCOPE,
        verdict.reasoning or "",
    )


# --------------------------------------------------------------------------- #
# 3. Query router
# --------------------------------------------------------------------------- #
def test_router():
    logger.info("=== Test 3: Query Router heuristics ===")

    check(
        "Greeting -> direct",
        query_router.route("hi").route == QueryRoute.DIRECT,
    )
    check(
        "Live exchange rate -> web_search",
        query_router.route("What is the current USD exchange rate right now?").route == QueryRoute.WEB_SEARCH,
    )
    check(
        "Surplus analytics -> rag",
        query_router.route("Show me the tomato surplus forecast for Dambulla").route == QueryRoute.RAG,
    )


# --------------------------------------------------------------------------- #
# 4. Web search tool markdown formatting (offline, no API key needed)
# --------------------------------------------------------------------------- #
def test_web_search_formatting():
    logger.info("=== Test 4: Web Search Tool markdown formatting ===")

    fake = WebSearchResponse(
        query="USD to LKR exchange rate",
        answer="1 USD is approximately 302 LKR.",
        results=[
            SearchResult(
                title="Central Bank of Sri Lanka - Exchange Rates",
                url="https://www.cbsl.gov.lk/rates",
                content="Indicative rate: 1 USD = 302.15 LKR.",
                score=0.94,
            )
        ],
    )
    md = web_search_tool.format_results_as_markdown(fake)

    check("Markdown contains the query", "USD to LKR exchange rate" in md)
    check("Markdown contains the summary answer", "302 LKR" in md)
    check("Markdown contains the source URL", "https://www.cbsl.gov.lk/rates" in md)


# --------------------------------------------------------------------------- #
# 5. End-to-end pipeline with a stubbed search tool + stubbed LLM
# --------------------------------------------------------------------------- #
def test_pipeline_end_to_end():
    logger.info("=== Test 5: End-to-end pipeline routing ===")

    search_calls = {"count": 0}

    class StubLLM:
        def invoke(self, messages, *_a, **_kw):
            class R:
                content = "Stubbed grounded answer."
            return R()

    def stub_search(query, max_results=5, include_answer=True, search_depth="basic"):
        search_calls["count"] += 1
        return WebSearchResponse(
            query=query,
            answer="1 USD is approximately 302 LKR.",
            results=[
                SearchResult(
                    title="CBSL Exchange Rates",
                    url="https://www.cbsl.gov.lk/rates",
                    content="1 USD = 302.15 LKR",
                    score=0.9,
                )
            ],
        )

    original_search = web_search_tool.search
    web_search_tool.search = stub_search

    pipeline = ConversationPipeline(rag_handler=lambda q: "Stubbed RAG analytics answer.")
    pipeline.direct_agent._llm = StubLLM()

    try:
        # 5a. Out-of-scope -> short-circuit, no search, no RAG
        t0 = time.perf_counter()
        res = pipeline.run("Write me a python script to debug javascript programming errors")
        elapsed = time.perf_counter() - t0
        check("Out-of-scope short-circuits pipeline", res.short_circuited is True)
        check("Out-of-scope returns static refusal", res.answer == OUT_OF_SCOPE_REPLY.strip())
        check("Out-of-scope performs no web search", res.search_performed is False)
        check("Out-of-scope is sub-second", elapsed < 1.0, f"{elapsed * 1000:.1f} ms")

        # 5b. Greeting -> direct route, zero search calls
        before = search_calls["count"]
        res = pipeline.run("hello")
        check("Greeting takes the direct route", res.route == QueryRoute.DIRECT.value, str(res.route))
        check("Greeting skips the search tool", search_calls["count"] == before)
        check("Greeting produces an answer", bool(res.answer))

        # 5c. Real-time query -> web_search route, search tool invoked
        before = search_calls["count"]
        res = pipeline.run("What is the current USD exchange rate right now?")
        check("Real-time query takes the web_search route", res.route == QueryRoute.WEB_SEARCH.value, str(res.route))
        check("web_search route calls the Tavily tool", search_calls["count"] == before + 1)
        check("web_search route returns source URLs", len(res.sources) > 0)

        # 5d. Domain analytics -> rag route
        before = search_calls["count"]
        res = pipeline.run("Show me the tomato surplus forecast for Dambulla")
        check("Domain query takes the rag route", res.route == QueryRoute.RAG.value, str(res.route))
        check("rag route skips the search tool", search_calls["count"] == before)
        check("rag handler answer is returned", res.answer == "Stubbed RAG analytics answer.")
    finally:
        web_search_tool.search = original_search


def main():
    logger.info("Running Guardrail + Direct Web Search smoke tests...\n")

    test_guardrail_classification()
    test_guardrail_fail_open()
    test_router()
    test_web_search_formatting()
    test_pipeline_end_to_end()

    passed = sum(1 for _, s in results if s == PASS)
    total = len(results)
    logger.info("\n" + "=" * 60)
    logger.info(f"RESULT: {passed}/{total} checks passed")
    for name, status in results:
        if status == FAIL:
            logger.error(f"  FAILED: {name}")
    logger.info("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
