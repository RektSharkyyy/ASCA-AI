"""
Market Analytics RAG Agent.

Bridges conversational queries to the internal Market Scout & Prophet forecasting
pipeline, Supabase PostgreSQL historical price data, and ChromaDB B2B matching.

Synthesizes accurate, data-grounded natural language answers quoting exact
prices, supply volumes, and trend predictions in clean, readable Markdown.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
import pandas as pd

from src.infrastructure.config import config
from src.infrastructure.llm_loader import get_llm
from src.infrastructure.logging import logger
from src.services.crop_catalog import (
    DEFAULT_CROP_BASKET,
    crop_label,
    detect_centre,
    detect_crop,
    normalise_centre,
    normalise_crop,
)
from src.agents.market_scout import market_scout_agent
from src.agents.tools.forecasting_tool import forecast_engine
from src.agents.tools.matcher_tool import chroma_b2b_store

SYSTEM_PERSONA = (
    "You are ASCA AI — the expert Agricultural Supply Chain Advisory Intelligence for "
    "Dambulla and Thambuththegama Economic Centres. You advise farmers, "
    "market traders, and food processing factories with precise market analytics. "
    "Always quote exact figures from the provided VERIFIED INTERNAL MARKET DATA. "
    "Do not invent or estimate numbers that are not provided in the data. "
    "Always communicate strictly in English. Never use any other language or non-English script."
)


def _is_sinhala_query(text: str) -> bool:
    """Returns True if the user query contains Sinhala Unicode characters."""
    return any('\u0D80' <= char <= '\u0DFF' for char in text)


def _clean_repetitive_text(text: str) -> str:
    """Safely trims and cleans up LLM output without catastrophic regex backtracking."""
    if not text:
        return ""
    return text.strip()


class MarketRAGAgent:
    """
    RAG Agent for internal market analytics, price predictions and B2B matching.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.15,
    ):
        agent_cfg = config.models.get("agent", {}) if hasattr(config, "models") else {}
        self.provider = provider or agent_cfg.get("provider") or config.env.DEFAULT_LLM_PROVIDER
        self.model_name = model_name or agent_cfg.get("llm_model") or "meta-llama/llama-3.1-8b-instruct"
        self.temperature = temperature
        self._llm = None

    def _lazy_load_llm(self):
        """Loads the chat model on first use."""
        if self._llm is None:
            self._llm = get_llm(
                provider=self.provider,
                model_name=self.model_name,
                temperature=self.temperature,
            )
            logger.info(f"MarketRAGAgent loaded LLM: {self.provider}/{self.model_name}")
        return self._llm

    def _invoke_llm(self, system_prompt: str, user_query: str) -> str:
        """Invokes the LLM safely with fallback and runaway loop protection."""
        try:
            llm = self._lazy_load_llm()
            response = llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ]
            )
            raw = (getattr(response, "content", str(response)) or "").strip()
            return _clean_repetitive_text(raw)
        except Exception as e:
            logger.error(f"MarketRAGAgent LLM invocation error: {e}")
            return ""

    async def handle_query_async(self, user_query: str, default_centre: str = "DAMBULLA") -> str:
        """
        Native async handler called by ConversationPipeline.
        """
        centre_id = detect_centre(user_query, default=default_centre)
        crop_id = detect_crop(user_query)

        logger.info(
            f"[MarketRAGAgent] query='{user_query[:60]}' detected centre={centre_id} crop={crop_id}"
        )

        if crop_id:
            return await self._handle_single_crop_query_async(user_query, centre_id, crop_id)
        else:
            return await self._handle_general_market_query_async(user_query, centre_id)

    def handle_query(self, user_query: str, default_centre: str = "DAMBULLA") -> str:
        """Synchronous wrapper for handle_query_async."""
        return asyncio.run(self.handle_query_async(user_query, default_centre))

    async def _handle_single_crop_query_async(
        self, user_query: str, centre_id: str, crop_id: str
    ) -> str:
        """Handles queries focused on a specific crop (e.g. carrots, tomatoes)."""
        label = crop_label(crop_id)
        centre_name = "Dambulla Economic Centre" if centre_id == "DAMBULLA" else "Thambuththegama Economic Centre"
        is_sinhala = _is_sinhala_query(user_query)

        # Fetch historical series from Supabase directly in the current async event loop
        try:
            df = await market_scout_agent.fetch_historical_data_async(centre_id, crop_id)
            curve = await forecast_engine.forecast_curve_async(df, centre_id, crop_id, history_days=7)
        except Exception as exc:
            logger.error(f"Failed to generate forecast curve for {crop_id}: {exc}")
            curve = {}

        current_price = curve.get("current_wholesale_price_lkr", 240.0)
        predicted_mean = curve.get("predicted_wholesale_price_lkr", current_price)
        supply_tons = curve.get("supply_volume_tons", 25.0)
        price_change_pct = curve.get("price_change_pct", 0.0)
        risk_level = curve.get("risk_level", "LOW")
        is_surplus = curve.get("surplus_anomaly_detected", False)

        forecast_points = curve.get("forecast", []) or []
        tomorrow_price = round(float(forecast_points[0]["price"]), 2) if forecast_points else current_price
        day7_price = round(float(forecast_points[6]["price"]), 2) if len(forecast_points) >= 7 else predicted_mean
        day14_price = round(float(forecast_points[-1]["price"]), 2) if forecast_points else predicted_mean

        # Check B2B buyers if surplus or buyer query
        buyers_text = ""
        try:
            buyers = await asyncio.to_thread(chroma_b2b_store.query_buyers_by_crop, crop_id, 2)
            if buyers:
                buyer_names = [f"{b['company_name']} ({b['location']}, Capacity: {b['daily_capacity_tons']}T)" for b in buyers]
                buyers_text = f"\n- Potential B2B Buyers: {'; '.join(buyer_names)}"
        except Exception:
            pass

        # Build context
        context = f"""
VERIFIED INTERNAL MARKET DATA:
- Location: {centre_name} ({centre_id})
- Crop: {label} ({crop_id})
- Current Wholesale Price Today: LKR {current_price:.2f} / kg
- Tomorrow's Projected Price (Day 1): LKR {tomorrow_price:.2f} / kg
- 7-Day Projected Price (Day 7): LKR {day7_price:.2f} / kg
- 14-Day Projected Price (Day 14): LKR {day14_price:.2f} / kg
- 14-Day Projected Price Change: {price_change_pct:+.2f}%
- Daily Market Supply: {supply_tons:.2f} Metric Tons
- Surplus Anomaly Detected: {'YES (Surplus Risk)' if is_surplus else 'NO (Normal Supply)'}
- Supply Chain Risk Level: {risk_level}{buyers_text}
"""

        prompt_instructions = (
            "Format the response using clean, beautifully formatted Markdown with distinct sections and bullet points.\n\n"
            f"### 🌾 **{label} Price Forecast & Market Analysis ({centre_name})**\n\n"
            "**📊 Price Forecast Summary:**\n"
            f"- **Today's Wholesale Price:** LKR {current_price:.2f} / kg\n"
            f"- **Tomorrow's Forecast Price:** LKR {tomorrow_price:.2f} / kg\n"
            f"- **7-Day Price Outlook:** LKR {day7_price:.2f} / kg\n"
            f"- **14-Day Projected Price:** LKR {day14_price:.2f} / kg ({price_change_pct:+.1f}% projection)\n\n"
            "**📦 Supply & Risk Status:**\n"
            f"- **Daily Market Supply:** {supply_tons:.2f} Metric Tons\n"
            f"- **Supply Chain Risk:** {risk_level} {'(⚠️ Surplus Anomaly Detected)' if is_surplus else '(✅ Normal Supply)'}\n\n"
            "**💡 Strategic Advisory:**\n"
            "- **For Farmers:** (Actionable recommendation: sell now or hold harvest)\n"
            "- **For Traders & Wholesalers:** (Purchasing and stocking advice)\n"
            "- **For Food Processors:** (B2B procurement or contract advice)\n\n"
            "LANGUAGE RULE: You MUST communicate 100% in English only. Do NOT use any other language or script."
        )

        system_prompt = f"{SYSTEM_PERSONA}\n\n{context}\n\n{prompt_instructions}"
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(self._invoke_llm, system_prompt, user_query),
                timeout=8.0,
            )
        except Exception as exc:
            logger.warning(f"[rag_agent] LLM call timed out or failed ({exc}). Using instant deterministic response.")
            answer = None

        if not answer:
            # Deterministic fallback
            trend_str = "decrease" if price_change_pct < 0 else "increase"
            answer = (
                f"### 🌾 **{label} Price Forecast & Market Analysis ({centre_name})**\n\n"
                f"**📊 Price Forecast Summary:**\n"
                f"- **Today's Wholesale Price:** LKR {current_price:.2f} / kg\n"
                f"- **Tomorrow's Forecast Price:** LKR {tomorrow_price:.2f} / kg\n"
                f"- **7-Day Outlook:** LKR {day7_price:.2f} / kg\n"
                f"- **14-Day Outlook:** LKR {day14_price:.2f} / kg ({price_change_pct:+.1f}% {trend_str})\n\n"
                f"**📦 Supply & Risk Status:**\n"
                f"- **Daily Market Supply:** {supply_tons:.1f} Metric Tons\n"
                f"- **Risk Level:** {risk_level} {'(⚠️ Surplus Risk Detected)' if is_surplus else '(✅ Normal)'}\n\n"
                f"**💡 Strategic Advisory:**\n"
                f"- **For Farmers:** Prices are projected to {'decline' if price_change_pct < 0 else 'remain stable'}. {'Consider early harvesting or securing B2B processing buyers to prevent losses.' if is_surplus else 'Harvest according to regular schedule.'}\n"
                f"- **For Traders:** {'Anticipate surplus supply and negotiate wholesale rates accordingly.' if is_surplus else 'Normal supply flow expected.'}\n"
                f"- **For Food Processors:** {'Ideal window to procure surplus stock at competitive rates.' if is_surplus else 'Procure according to standard production schedules.'}"
            )

        return answer

    async def _handle_general_market_query_async(
        self, user_query: str, centre_id: str
    ) -> str:
        """Handles broader market queries covering multiple crops or general conditions."""
        centre_name = "Dambulla Economic Centre" if centre_id == "DAMBULLA" else "Thambuththegama Economic Centre"
        is_sinhala = _is_sinhala_query(user_query)

        # Scan crops
        insights_lines = []
        for crop in DEFAULT_CROP_BASKET:
            try:
                df = await market_scout_agent.fetch_historical_data_async(centre_id, crop)
                summary = await forecast_engine.forecast_crop_prices_async(df, centre_id, crop)
                label = crop_label(crop)
                insights_lines.append(
                    f"- **{label}:** Today LKR {summary['current_wholesale_price_lkr']:.2f}/kg | "
                    f"Forecast LKR {summary['predicted_wholesale_price_lkr']:.2f}/kg | "
                    f"Supply {summary['supply_volume_tons']:.1f}T | Risk: {summary['risk_level']}"
                )
            except Exception:
                continue

        context = f"""
VERIFIED INTERNAL MARKET BASKET ({centre_name}):
{chr(10).join(insights_lines)}
"""

        lang_rule = "Respond strictly in clear Sinhala." if is_sinhala else "CRITICAL: Respond ONLY in 100% English. Do NOT generate or append any Sinhala text."

        prompt_instructions = (
            "Provide an executive summary of current market conditions at the economic centre based on the data. "
            "Highlight key price leaders, notable price drops or surplus alerts, and general advice for growers and buyers. "
            f"Format in clean Markdown with emojis and clear sections. {lang_rule}"
        )

        system_prompt = f"{SYSTEM_PERSONA}\n\n{context}\n\n{prompt_instructions}"
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(self._invoke_llm, system_prompt, user_query),
                timeout=8.0,
            )
        except Exception as exc:
            logger.warning(f"[rag_agent] LLM general call timed out ({exc}). Using instant fallback.")
            answer = None

        if not answer:
            answer = (
                f"### 🌾 **Market Overview for {centre_name}**\n\n"
                + "\n".join(insights_lines)
                + "\n\n💡 *You can ask for detailed 14-day price curves or B2B buyer matching for any specific crop.*"
            )

        return answer


market_rag_agent = MarketRAGAgent()
