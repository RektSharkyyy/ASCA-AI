"""
Chat API route.

POST /api/chat
  Receives a user message + active economic centre, runs it through the full
  ConversationPipeline (guardrail → router → agent/RAG), and returns a rich
  ChatResponse that the frontend renders directly.
"""

import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.auth.dependencies import get_current_user
from src.infrastructure.models import UserModel

from src.agents.pipeline import conversation_pipeline
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    ChartPayload,
    ForecastPoint,
    InlineAction,
    ThoughtStep,
)
from src.infrastructure.logging import logger
from src.services.crop_catalog import detect_centre, detect_crop, crop_label
from src.services.market_service import market_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_thoughts(route: str | None, in_scope: bool, search_performed: bool) -> List[ThoughtStep]:
    """Synthesises the agent reasoning steps the UI shows in the thought-log."""
    thoughts: List[ThoughtStep] = []
    if not in_scope:
        thoughts.append(ThoughtStep(tool="Domain Guardrail", detail="Query classified OUT_OF_SCOPE — static refusal returned."))
        return thoughts

    thoughts.append(ThoughtStep(tool="Domain Guardrail", detail="Query classified IN_SCOPE — proceeding to router."))

    if route == "direct":
        thoughts.append(ThoughtStep(tool="Query Router", detail="Routed to DirectAgent (greeting / chitchat)."))
    elif route == "web_search":
        thoughts.append(ThoughtStep(tool="Query Router", detail="Routed to web_search — real-time external information requested."))
        thoughts.append(ThoughtStep(tool="Tavily Web Search", detail="Live web results fetched and grounded into answer." if search_performed else "Web search skipped."))
    elif route == "rag":
        thoughts.append(ThoughtStep(tool="Query Router", detail="Routed to RAG pipeline — internal market analytics."))
        thoughts.append(ThoughtStep(tool="Market Scout Agent", detail="Prophet 14-day forecast + surplus anomaly detection running."))
        thoughts.append(ThoughtStep(tool="Pydantic Guardrail", detail="MarketInsight schema validated."))

    return thoughts


def _build_actions(route: str | None, has_chart: bool) -> List[InlineAction]:
    """Builds context-aware suggested follow-up actions."""
    if route == "rag" and has_chart:
        return [
            InlineAction(label="Find B2B Buyers", icon="ext", primary=True,
                         prompt="Find B2B buyers for current surplus"),
            InlineAction(label="Generate Blueprint", icon="pdf",
                         prompt="Generate executive advisory blueprint"),
            InlineAction(label="Broadcast SMS Alert", icon="sms"),
        ]
    if route == "rag":
        return [
            InlineAction(label="Show Price Forecast", icon="chart", primary=True,
                         prompt="Show tomato price forecast"),
            InlineAction(label="Generate Blueprint", icon="pdf",
                         prompt="Generate executive advisory blueprint"),
        ]
    return []


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
) -> ChatResponse:
    """
    Main conversational endpoint.

    Runs the multi-agent pipeline and enriches the response with:
    - Agent thought log
    - Inline action suggestions
    - Optional price-forecast chart (when the RAG route detects a crop mention)
    """
    t0 = time.perf_counter()
    session_id = req.session_id or str(uuid.uuid4())

    # Detect centre from message text; fall back to the UI selection.
    effective_centre = detect_centre(req.message, default=req.centre_id)

    logger.info(f"[chat] session={session_id} centre={effective_centre} message='{req.message[:80]}'")

    try:
        result = await conversation_pipeline.run_async(req.message, centre_id=effective_centre)
    except Exception as exc:
        logger.error(f"[chat] pipeline error: {exc}")
        raise HTTPException(status_code=500, detail="Agent pipeline failed. Please try again.")

    # ------------------------------------------------------------------ #
    # Optional chart: attach whenever a crop is mentioned on the RAG route
    # ------------------------------------------------------------------ #
    chart: ChartPayload | None = None
    if result.route == "rag":
        crop_name = detect_crop(req.message)
        if crop_name:
            try:
                forecast = await market_service.get_forecast(effective_centre, crop_name)
                chart = ChartPayload(
                    crop=forecast.crop_label,
                    centre_id=forecast.centre_id,
                    unit="LKR/kg",
                    data=forecast.series,
                )
            except Exception as exc:
                logger.warning(f"[chat] chart generation skipped: {exc}")

    latency_ms = int((time.perf_counter() - t0) * 1000)

    return ChatResponse(
        session_id=session_id,
        query=result.query,
        answer=result.answer,
        route=result.route,
        in_scope=result.in_scope,
        short_circuited=result.short_circuited,
        search_performed=result.search_performed,
        sources=result.sources,
        thoughts=_build_thoughts(result.route, result.in_scope, result.search_performed),
        actions=_build_actions(result.route, chart is not None),
        chart=chart,
        latency_ms=latency_ms,
    )
