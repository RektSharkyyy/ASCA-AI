"""
Chat API route.

POST /api/chat
  Receives a user message + active economic centre, runs it through the full
  ConversationPipeline (guardrail → router → agent/RAG), persists the
  exchange to `chat_history`, and returns a rich ChatResponse.

GET  /api/chat/history
  Returns a list of the current user's conversation session summaries.

GET  /api/chat/history/{session_id}
  Returns all messages in a specific session (current user only).

DELETE /api/chat/history/{session_id}
  Deletes a specific conversation session (current user only).

DELETE /api/chat/history
  Clears ALL history for the current user.
"""

import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.infrastructure.db import get_db_session
from src.infrastructure.models import ChatHistoryModel, UserModel

from src.agents.pipeline import conversation_pipeline
from src.api.schemas import (
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
    ChatSessionSummary,
    ChartPayload,
    ForecastPoint,
    InlineAction,
    ThoughtStep,
)
from src.infrastructure.logging import logger
from src.services.crop_catalog import detect_centre, detect_crop, crop_label
from src.services.market_service import market_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# POST /api/chat  — main conversational endpoint
# --------------------------------------------------------------------------- #

@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    """
    Main conversational endpoint.

    Runs the multi-agent pipeline, enriches the response, then persists the
    exchange to `chat_history` bound to the authenticated user's ID.
    """
    t0 = time.perf_counter()
    session_id = req.session_id or str(uuid.uuid4())

    # Detect centre from message text; fall back to the UI selection.
    effective_centre = detect_centre(req.message, default=req.centre_id)

    logger.info(f"[chat] user={current_user.id} session={session_id} centre={effective_centre} message='{req.message[:80]}'")

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

    # ------------------------------------------------------------------ #
    # Persist exchange to Supabase (chat_history table)
    # ------------------------------------------------------------------ #
    try:
        chart_json = chart.model_dump_json() if chart else None
        record = ChatHistoryModel(
            user_id    = current_user.id,
            session_id = session_id,
            centre_id  = effective_centre,
            query      = req.message,
            answer     = result.answer,
            route      = result.route,
            in_scope   = result.in_scope,
            chart_data = chart_json,
            latency_ms = latency_ms,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        logger.info(f"[chat] saved history record id={record.id} for user={current_user.id}")
    except Exception as exc:
        logger.warning(f"[chat] failed to persist chat history: {exc}")
        await db.rollback()

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


# --------------------------------------------------------------------------- #
# GET /api/chat/history  — list all sessions for the current user
# --------------------------------------------------------------------------- #

@router.get("/history", response_model=List[ChatSessionSummary])
async def get_chat_sessions(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[ChatSessionSummary]:
    """Returns a summary card per conversation session (newest first)."""

    stmt = (
        select(
            ChatHistoryModel.session_id,
            ChatHistoryModel.centre_id,
            func.count(ChatHistoryModel.id).label("message_count"),
            func.min(ChatHistoryModel.query).label("first_query"),
            func.max(ChatHistoryModel.created_at).label("last_message_at"),
        )
        .where(ChatHistoryModel.user_id == current_user.id)
        .group_by(ChatHistoryModel.session_id, ChatHistoryModel.centre_id)
        .order_by(func.max(ChatHistoryModel.created_at).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    summaries = []
    for row in rows:
        title = (row.first_query or "New Chat")[:60]
        summaries.append(ChatSessionSummary(
            session_id      = row.session_id,
            title           = title,
            message_count   = row.message_count,
            centre_id       = row.centre_id,
            last_message_at = row.last_message_at,
        ))

    return summaries


# --------------------------------------------------------------------------- #
# GET /api/chat/history/{session_id}  — full thread for a session
# --------------------------------------------------------------------------- #

@router.get("/history/{session_id}", response_model=List[ChatHistoryItem])
async def get_session_messages(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[ChatHistoryItem]:
    """Returns every message in a session. Only the owning user can access it."""

    stmt = (
        select(ChatHistoryModel)
        .where(
            ChatHistoryModel.user_id    == current_user.id,
            ChatHistoryModel.session_id == session_id,
        )
        .order_by(ChatHistoryModel.created_at.asc())
    )

    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        raise HTTPException(status_code=404, detail="Session not found.")

    return [
        ChatHistoryItem(
            id         = r.id,
            session_id = r.session_id,
            query      = r.query,
            answer     = r.answer,
            route      = r.route,
            in_scope   = r.in_scope,
            centre_id  = r.centre_id,
            chart_data = r.chart_data,
            latency_ms = r.latency_ms,
            created_at = r.created_at,
        )
        for r in records
    ]


# --------------------------------------------------------------------------- #
# DELETE /api/chat/history/{session_id}  — delete a specific session
# --------------------------------------------------------------------------- #

@router.delete("/history/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Deletes all messages in a session. Only the owning user can do this."""

    stmt = (
        delete(ChatHistoryModel)
        .where(
            ChatHistoryModel.user_id    == current_user.id,
            ChatHistoryModel.session_id == session_id,
        )
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found.")


# --------------------------------------------------------------------------- #
# DELETE /api/chat/history  — clear ALL history for the current user
# --------------------------------------------------------------------------- #

@router.delete("/history", status_code=204)
async def clear_all_history(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Wipes every chat record belonging to the authenticated user."""

    stmt = delete(ChatHistoryModel).where(
        ChatHistoryModel.user_id == current_user.id
    )
    await db.execute(stmt)
    await db.commit()
    logger.info(f"[chat] cleared all history for user={current_user.id}")
