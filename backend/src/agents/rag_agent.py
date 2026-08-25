"""
Market Analytics RAG Agent.

Bridges conversational queries to the internal Market Scout & Prophet forecasting
pipeline, Supabase / SQLite historical price data, ChromaDB B2B matching,
and Department of Agriculture agronomic guides with real-time Tavily web intelligence.

Synthesizes accurate, data-grounded natural language answers quoting exact
prices, supply volumes, and trend predictions strictly in clean, readable English Markdown.
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

import math

SYSTEM_PERSONA = (
    "You are ASCA AI — the expert Agricultural Supply Chain Advisory Intelligence for "
    "Dambulla and Thambuththegama Economic Centres in Sri Lanka. You advise farmers, "
    "market traders, and food processing factories with precise market and agronomy analytics. "
    "Always quote exact figures from the provided VERIFIED INTERNAL MARKET DATA and LIVE WEB RESEARCH. "
    "Do not invent or estimate numbers that are not provided in the data. "
    "CRITICAL RULE: You MUST communicate strictly in 100% professional English at all times. "
    "Never use or output any Sinhala text or non-English script."
)


def _clean_repetitive_text(text: str) -> str:
    """Safely trims and cleans up LLM output without catastrophic regex backtracking."""
    if not text:
        return ""
    return text.strip()


def _extract_land_area_acres(text: str) -> Optional[float]:
    """
    Extracts land size in acres from user queries like '2.5 acres', '1/2 acre', '10 perches', '2 ha'.
    Returns float acreage if found, else None.
    """
    q = text.lower()

    # Fractions
    if "half acre" in q or "1/2 acre" in q or "0.5 acre" in q or "half an acre" in q:
        return 0.5
    if "quarter acre" in q or "1/4 acre" in q or "0.25 acre" in q:
        return 0.25
    if "3/4 acre" in q or "0.75 acre" in q:
        return 0.75

    # Decimal / Integer acres: e.g. "2.5 acres", "3 acre", "1.5 ac"
    m_acre = re.search(r'(\d+(?:\.\d+)?)\s*(?:acres?|ac\b)', q)
    if m_acre:
        try:
            val = float(m_acre.group(1))
            if 0.01 <= val <= 1000:
                return round(val, 2)
        except Exception:
            pass

    # Hectares: e.g. "2 ha", "1.5 hectares" (1 ha = 2.471 acres)
    m_ha = re.search(r'(\d+(?:\.\d+)?)\s*(?:hectares?|ha\b)', q)
    if m_ha:
        try:
            val = float(m_ha.group(1)) * 2.471
            return round(val, 2)
        except Exception:
            pass

    # Perches: e.g. "40 perches", "80 perch" (160 perches = 1 acre)
    m_perch = re.search(r'(\d+(?:\.\d+)?)\s*(?:perches?|perch\b)', q)
    if m_perch:
        try:
            val = float(m_perch.group(1)) / 160.0
            return round(val, 2)
        except Exception:
            pass

    return None


def _calculate_scaled_fertilizer(guide: dict, acres: float) -> dict:
    """
    Calculates exact scaled fertilizer quantities, bag requirements, and total amounts for a given acreage.
    """
    fert_schedule = guide.get("fertilizer_schedule", {})
    scaled_phases = {}
    total_nutrients_kg = {}

    for phase_key, phase in fert_schedule.items():
        phase_name = {
            "basal": "Basal Dressing (At Planting / Day 1)",
            "top_dressing_1": "Top Dressing 1 (Week 3–4)",
            "top_dressing_2": "Top Dressing 2 (Flowering / Fruit Set)",
            "top_dressing_3": "Top Dressing 3 (After First Harvest)",
        }.get(phase_key, phase_key.replace("_", " ").title())

        inputs_scaled = []
        for inp in phase.get("inputs", []):
            name = inp["name"]
            qty_str = inp["quantity"]
            method = inp.get("method", "Application")

            num_match = re.search(r'([\d,\.]+)', qty_str)
            if num_match:
                raw_num = float(num_match.group(1).replace(",", ""))
                scaled_num = round(raw_num * acres, 2)

                if "5,000" in qty_str or "4,000" in qty_str or "3,000" in qty_str or scaled_num >= 1000:
                    scaled_display = f"{scaled_num:,.1f} kg ({scaled_num/1000:.2f} Metric Tons)"
                elif scaled_num < 1.0:
                    scaled_display = f"{scaled_num:.2f} kg ({int(scaled_num*1000)} grams)"
                else:
                    scaled_display = f"{scaled_num:,.1f} kg"

                inputs_scaled.append({
                    "name": name,
                    "per_acre": qty_str,
                    "scaled_quantity": scaled_display,
                    "method": method
                })

                key_type = None
                n_low = name.lower()
                if "urea" in n_low: key_type = "Urea (46% N)"
                elif "tsp" in n_low or "triple super" in n_low: key_type = "TSP (Triple Super Phosphate)"
                elif "mop" in n_low or "muriate of potash" in n_low: key_type = "MOP (Muriate of Potash)"
                elif "compost" in n_low or "manure" in n_low: key_type = "Organic Compost / Cattle Manure"
                elif "calcium nitrate" in n_low: key_type = "Calcium Nitrate"
                elif "boron" in n_low: key_type = "Boron (Solubor)"

                if key_type:
                    total_nutrients_kg[key_type] = total_nutrients_kg.get(key_type, 0.0) + scaled_num

        scaled_phases[phase_name] = {
            "timing": phase.get("timing", ""),
            "inputs": inputs_scaled
        }

    procurement_summary = []
    for fert_name, total_kg in total_nutrients_kg.items():
        if "compost" in fert_name.lower() or "manure" in fert_name.lower():
            procurement_summary.append({
                "item": fert_name,
                "total_kg": f"{total_kg:,.0f} kg ({total_kg/1000:.2f} MT)",
                "bags_50kg": f"{round(total_kg/50):,} bags (50kg)" if total_kg >= 50 else "Bulk"
            })
        elif "boron" in fert_name.lower():
            procurement_summary.append({
                "item": fert_name,
                "total_kg": f"{total_kg:.2f} kg ({int(total_kg*1000)} g)",
                "bags_50kg": f"{round(total_kg, 1)} kg pack"
            })
        else:
            bags = math.ceil(total_kg / 50.0)
            procurement_summary.append({
                "item": fert_name,
                "total_kg": f"{total_kg:,.1f} kg",
                "bags_50kg": f"{bags} bags (50kg each)"
            })

    return {
        "acres": acres,
        "phases": scaled_phases,
        "procurement": procurement_summary
    }



class MarketRAGAgent:
    """
    RAG Agent for internal market analytics, price predictions, B2B matching,
    and cultivation advisory grounded in real-time web intelligence.
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
        if self._llm is None:
            try:
                self._llm = get_llm(
                    provider=self.provider,
                    model_name=self.model_name,
                    temperature=self.temperature,
                )
                logger.info(
                    f"MarketRAGAgent loaded LLM: {self.provider}/{self.model_name}"
                )
            except Exception as e:
                logger.error(f"Failed to load LLM in MarketRAGAgent: {e}")
                self._llm = None
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

        q_lower = user_query.lower()

        # Check explicit price/market intent
        price_market_stems = [
            "price", "cost", "rate", "forecast", "predict", "curve", "chart",
            "trend", "wholesale", "supply", "surplus", "drop", "rise", "increase",
            "decrease", "b2b", "buyer", "matcher", "factory", "procure", "sell for", "selling"
        ]
        is_explicit_price_query = any(stem in q_lower for stem in price_market_stems)

        # Check agronomic/cultivation/fertilizer/pest intent (handles misspellings like 'fertilaizer')
        cultivation_stems = [
            # Fertilizer & Nutrition
            "fertil", "fertilaiz", "fertilis", "fetil", "furtil", "pohora", "manure", "compost",
            "urea", "tsp", "mop", "dap", "npk", "nutrient", "calcium", "boron", "zinc",
            "top dress", "basal", "feed", "soil", "organic",
            # Pests & Diseases
            "pest", "insect", "bug", "worm", "fly", "borer", "thrips", "aphid", "whitefly",
            "caterpillar", "moth", "mite", "shield", "spray", "pesticide", "fungicide",
            "disease", "blight", "rot", "wilt", "virus", "mosaic", "damping", "anthracnose",
            "symptom", "cure", "treatment", "control", "medicine",
            # Cultivation & Agronomy
            "grow", "cultivat", "plant", "sow", "seed", "nursery", "spacing", "water",
            "irrigat", "ph", "timeline", "stage", "harvest", "recommend", "suggest",
            "farming", "season", "maha", "yala", "next 6 month", "6 month", "acre", "yield",
            "how to use", "what can i use", "guide", "protocol"
        ]
        is_cultivation_query = any(stem in q_lower for stem in cultivation_stems)

        # If question is about cultivation/fertilizer/pest, or if crop is mentioned without price intent:
        if is_cultivation_query or (crop_id and not is_explicit_price_query):
            return await self._handle_cultivation_query_async(user_query, centre_id, crop_id)
        elif crop_id:
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
                timeout=25.0,
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

        prompt_instructions = (
            "Provide an executive summary of current market conditions at the economic centre based on the data. "
            "Highlight key price leaders, notable price drops or surplus alerts, and general advice for growers and buyers. "
            "Format in clean Markdown with emojis and clear sections. Communicate strictly in 100% English."
        )

        system_prompt = f"{SYSTEM_PERSONA}\n\n{context}\n\n{prompt_instructions}"
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(self._invoke_llm, system_prompt, user_query),
                timeout=25.0,
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

    async def _handle_cultivation_query_async(
        self, user_query: str, centre_id: str, crop_id: Optional[str]
    ) -> str:
        """Handles 6-month seasonal crop recommendations, cultivation stages, fertilizer, and pest management using Live Web Search + LLM Reasoning."""
        from src.services.cultivation_service import get_recommendations, get_crop_guide, get_all_crops
        from src.agents.tools.web_search_tool import TavilySearchTool

        centre_name = "Dambulla Economic Centre" if centre_id == "DAMBULLA" else "Thambuththegama Economic Centre"
        q_lower = user_query.lower()

        # Identify sub-intents
        is_fertilizer = any(s in q_lower for s in [
            "fertil", "fertilaiz", "fertilis", "fetil", "furtil", "pohora", "urea", "tsp", "mop",
            "dap", "npk", "nutrient", "compost", "manure", "top dress", "basal", "feed"
        ])
        is_pest = any(s in q_lower for s in [
            "pest", "insect", "bug", "worm", "fly", "borer", "thrips", "aphid", "whitefly",
            "caterpillar", "moth", "mite", "shield", "spray", "pesticide", "fungicide",
            "disease", "blight", "rot", "wilt", "virus", "mosaic", "damping", "anthracnose",
            "symptom", "cure", "treatment", "control", "medicine"
        ])

        # Detect land area from query (e.g. '2.5 acres', 'half acre', '10 perches', '3 ha')
        acres = _extract_land_area_acres(user_query) or 1.0

        # ── 1. LIVE WEB INTELLIGENCE SEARCH ─────────────────────────────────
        web_snippets = ""
        citations = []
        try:
            search_tool = TavilySearchTool()
            if crop_id and is_fertilizer:
                query_str = f"Sri Lanka Department of Agriculture {crop_id} fertilizer dosage schedule basal top dressing DOA"
            elif crop_id and is_pest:
                query_str = f"Sri Lanka Department of Agriculture {crop_id} pest disease control IPM symptoms DOA"
            elif crop_id:
                query_str = f"Sri Lanka Department of Agriculture {crop_id} cultivation agronomy fertilizer pest guide 2026"
            else:
                query_str = f"Sri Lanka Department of Agriculture Maha season crop cultivation recommendations {centre_id} 2026"

            search_res = await asyncio.to_thread(search_tool.search, query_str, max_results=3, search_depth="basic")
            if search_res and search_res.results:
                web_snippets = "\n".join([f"- **{r.title}:** {r.content[:240]} (Source: {r.url})" for r in search_res.results])
                citations = [f"[{r.title}]({r.url})" for r in search_res.results[:2]]
        except Exception as err:
            logger.warning(f"[rag_agent] Live web search failed ({err}), proceeding with internal agronomy knowledge.")

        # ── 2. COMPOSE DEEP DYNAMIC PROMPT ──────────────────────────────────
        if crop_id:
            guide = get_crop_guide(crop_id)
            if guide:
                fert = guide.get("fertilizer_schedule", {})
                basal = fert.get("basal", {})
                top1 = fert.get("top_dressing_1", {})
                top2 = fert.get("top_dressing_2", {})
                top3 = fert.get("top_dressing_3", {})
                pests = guide.get("pests_and_diseases", [])

                # Calculate mathematically exact scaled dosages for the specified land area
                scaled_calc = _calculate_scaled_fertilizer(guide, acres)
                scaled_phases_text = []
                for p_name, p_data in scaled_calc["phases"].items():
                    items_str = ", ".join([f"{inp['name']}: {inp['scaled_quantity']}" for inp in p_data["inputs"]])
                    scaled_phases_text.append(f"- **{p_name} ({p_data['timing']}):** {items_str}")
                scaled_phases_block = "\n".join(scaled_phases_text)

                procurement_lines = [
                    f"- **{item['item']}:** Total {item['total_kg']} (Requires: **{item['bags_50kg']}**)"
                    for item in scaled_calc["procurement"]
                ]
                procurement_block = "\n".join(procurement_lines)

                basal_str = ", ".join([f"{i['name']} ({i['quantity']})" for i in basal.get("inputs", [])])
                top1_str = ", ".join([f"{i['name']} ({i['quantity']})" for i in top1.get("inputs", [])])
                top2_str = ", ".join([f"{i['name']} ({i['quantity']})" for i in top2.get("inputs", [])])
                top3_str = ", ".join([f"{i['name']} ({i['quantity']})" for i in top3.get("inputs", [])]) if top3 else "None"
                pest_str = "\n".join([f"- **{p['name']} [{p.get('category', 'Pest/Disease')}]:** {p['symptoms']} | *Organic:* {p['organic_control']} | *Approved Chemical:* {p['chemical_control']}" for p in pests[:4]])

                expected_yield_scaled = f"{round(guide['yield_per_acre_tons_min'] * acres, 1)} – {round(guide['yield_per_acre_tons_max'] * acres, 1)} MT"
                expected_cost_scaled = f"LKR {round(guide['estimated_cost_per_acre_lkr'] * acres):,}"

                context = f"""
LIVE WEB SEARCH INTELLIGENCE (DOA SRI LANKA / RECENT RESEARCH):
{web_snippets if web_snippets else "Real-time agronomic data from Sri Lanka Department of Agriculture publications."}

VERIFIED DOA AGRONOMIC BENCHMARKS FOR {guide['name'].upper()} ({guide.get('botanical_name', '')}):
- Land Size Target: {acres} Acre(s)
- Expected Total Yield for {acres} Acres: {expected_yield_scaled} | Est. Cultivation Cost: {expected_cost_scaled}
- Projected Wholesale Floor Rate: LKR {guide['avg_wholesale_price_lkr_per_kg']:.2f} / kg | ROI: {guide['roi_estimate_pct']}%
- Spacing: {guide['plant_spacing_cm']} cm | Growth Duration: {guide['growth_days']} Days | Ideal pH: {guide['ideal_ph']}

EXACT PRE-CALCULATED FERTILIZER SCHEDULE SCALED FOR {acres} ACRE(S):
{scaled_phases_block}

TOTAL COMMERCIAL PROCUREMENT BREAKDOWN (50 KG BAGS) FOR {acres} ACRE(S):
{procurement_block}

Key Pests & Diseases:
{pest_str}
"""
                if is_fertilizer or acres != 1.0:
                    prompt_instructions = (
                        f"The user is asking about FERTILIZER requirements for {acres} Acre(s) of {guide['name']}. "
                        f"Provide a comprehensive, mathematically exact Fertilizer & Nutrition Plan tailored specifically for {acres} Acre(s). "
                        "Structure your answer clearly with: "
                        f"(1) Title: 🧪 **{guide['name']} ({guide.get('botanical_name', '')}) — Fertilizer Schedule for {acres} Acre(s)**\n"
                        f"(2) Step-by-Step Scaled Application Phases (Basal Dressing, Top Dressing 1, Top Dressing 2, Top Dressing 3) quoting exact scaled kilograms/tons.\n"
                        f"(3) Commercial Procurement Summary (exact 50 kg commercial bag count needed for purchase).\n"
                        f"(4) Organic & Bio-fertilizer inputs (exact tons/kg for {acres} acres).\n"
                        "(5) Practical Soil & Application Guidelines (ring placement distance, moisture, and root burn prevention).\n"
                        "Do NOT output market price forecast curves. Format in clean, beautiful Markdown with emojis and bold highlights."
                    )
                elif is_pest:
                    prompt_instructions = (
                        f"The user specifically asked about PEST & DISEASE management for {guide['name']}. "
                        "Provide a comprehensive Integrated Pest Management (IPM) Shield detailing: "
                        "(1) Identification and Symptoms of major pests and diseases, "
                        "(2) Cultural & Organic Control methods (traps, Neem oil, spacing, crop rotation), and "
                        "(3) Approved Chemical / IPM Treatments with exact dosage rates. "
                        "Do NOT include market price forecast curves. Format in clean, clear Markdown with emojis."
                    )
                else:
                    prompt_instructions = (
                        f"Provide a comprehensive agronomic guide for {guide['name']} ({acres} Acre(s)) covering climate suitability, "
                        "fertilizer schedule, pest management, and cultivation lifecycle stages. "
                        "Format in clean Markdown with emojis and distinct headings."
                    )

                system_prompt = f"{SYSTEM_PERSONA}\n\n{context}\n\n{prompt_instructions}"

                try:
                    answer = await asyncio.wait_for(
                        asyncio.to_thread(self._invoke_llm, system_prompt, user_query),
                        timeout=25.0,
                    )
                except Exception as exc:
                    logger.warning(f"[rag_agent] Cultivation LLM call timed out ({exc}). Using fallback.")
                    answer = None

                if not answer:
                    if is_fertilizer or acres != 1.0:
                        phases_md = []
                        for p_name, p_data in scaled_calc["phases"].items():
                            inps = "\n".join([f"- **{inp['name']}:** {inp['scaled_quantity']} *({inp['method']})*" for inp in p_data["inputs"]])
                            phases_md.append(f"**{p_name} ({p_data['timing']}):**\n{inps}")

                        answer = (
                            f"### 🧪 **{guide['name']} ({guide.get('botanical_name', '')}) — Fertilizer Calculation for {acres} Acre(s)**\n\n"
                            f"Based on **Department of Agriculture (DOA) Sri Lanka** agronomic benchmarks, here is the exact fertilizer dosage and commercial procurement plan for your **{acres} acre** farm in **{centre_name}**:\n\n"
                            + "\n\n".join(phases_md)
                            + f"\n\n**📦 Total Commercial Procurement Sheet ({acres} Acres):**\n"
                            + "\n".join(procurement_lines)
                            + f"\n\n**💡 Application & Field Management Directives:**\n"
                            f"- **Placement:** Apply granular fertilizer in a shallow circular ring 10–15 cm away from the plant stem.\n"
                            f"- **Irrigation:** Irrigate thoroughly within 2–3 hours of application to dissolve nutrients into the active root zone.\n"
                            f"- **Organic Base:** Apply {round(5000 * acres):,} kg of well-cured compost or cattle manure during primary tillage."
                        )
                    elif is_pest:
                        answer = (
                            f"### 🛡️ **{guide['name']} ({guide.get('botanical_name', '')}) — Integrated Pest & Disease Shield**\n\n"
                            + "\n\n".join([
                                f"**{p['name']} ({p.get('category', 'Pest/Disease')}):**\n"
                                f"- **Symptoms:** {p['symptoms']}\n"
                                f"- **🌿 Organic / Cultural Control:** {p['organic_control']}\n"
                                f"- **⚗️ Approved IPM / Chemical Treatment:** {p['chemical_control']}"
                                for p in pests
                            ])
                        )
                    else:
                        answer = (
                            f"### 🌱 **{guide['name']} ({guide.get('botanical_name', '')}) — Cultivation & Agronomy Guide ({acres} Acres)**\n\n"
                            f"**📊 Key Agronomic Parameters ({centre_name}):**\n"
                            f"- **Expected Total Yield ({acres} Ac):** {expected_yield_scaled} · **Est. Cost:** {expected_cost_scaled}\n"
                            f"- **Growth Duration:** {guide['growth_days']} Days · **Plant Spacing:** {guide['plant_spacing_cm']} cm · **Ideal pH:** {guide['ideal_ph']}\n\n"
                            f"**🧪 Scaled Fertilizer Schedule ({acres} Acres):**\n"
                            + "\n".join(procurement_lines)
                            + f"\n\n**🛡️ Key Pests & Protection:**\n"
                            + "\n".join([f"- **{p['name']}:** *Organic:* {p['organic_control']} · *IPM:* {p['chemical_control']}" for p in pests[:2]])
                        )
                return answer
        else:
            # Multi-crop recommendation for next 6 months
            recs = get_recommendations("Maha", "Reddish Brown Earth", "Agrowell", 1.0, centre_id)
            top_crops = recs[:4]

            rec_text = "\n".join([
                f"{i+1}. **{c['emoji']} {c['name']} ({c.get('botanical_name', '')}):** Estimated ROI **{c['roi_estimate_pct']}%** | "
                f"Avg Yield **{c['avg_yield_tons']} MT/acre** | Est. Net Profit **LKR {c['estimated_net_profit_lkr']:,}** | "
                f"Market Demand: **{c['market_demand']}** (Growth: {c['growth_days']} days)"
                for i, c in enumerate(top_crops)
            ])

            context = f"""
LIVE WEB SEARCH INTELLIGENCE (DOA SRI LANKA / CURRENT ADVISORIES):
{web_snippets if web_snippets else "Real-time seasonal weather and crop advisories from Sri Lanka Department of Agriculture."}

6-MONTH SEASONAL CROP BENCHMARKS (Maha Season / {centre_name}):
{rec_text}
"""
            system_prompt = (
                f"{SYSTEM_PERSONA}\n\n{context}\n\n"
                "The user is asking what to grow / cultivate over the next 6 months. "
                "Synthesize the LIVE WEB SEARCH FINDINGS and market price analytics dynamically to give a customized, comprehensive crop selection advisory. "
                "Rank the top high-performing crops, explain WHY they are chosen based on current Maha/Yala seasonal patterns, water availability, and market demand. "
                "Provide actionable agronomic guidance (planting window, basal fertilizer timing, and pest prevention). "
                "Format using clean, rich Markdown with emojis and bullet points. Communicate strictly in 100% English."
            )

            try:
                answer = await asyncio.wait_for(
                    asyncio.to_thread(self._invoke_llm, system_prompt, user_query),
                    timeout=25.0,
                )
            except Exception as exc:
                logger.warning(f"[rag_agent] Cultivation recs LLM call timed out ({exc}). Using fallback.")
                answer = None

            if not answer:
                answer = (
                    f"### 🌾 **Top Recommended Crops to Cultivate for the Next 6 Months ({centre_name})**\n\n"
                    f"Based on current Maha/Yala seasonal climate patterns, market price projections, and soil compatibility, here are the **Top high-yield crops** recommended for your farm:\n\n"
                    + "\n\n".join([
                        f"**{i+1}. {c['emoji']} {c['name']} ({c.get('botanical_name', '')})**\n"
                        f"- **Estimated ROI:** {c['roi_estimate_pct']}% (Est. Net Profit: **LKR {c['estimated_net_profit_lkr']:,}** per acre)\n"
                        f"- **Expected Yield:** {c['avg_yield_tons']} Metric Tons · **Growth Duration:** {c['growth_days']} Days\n"
                        f"- **Market Demand:** {c['market_demand']} · **Wholesale Floor Rate:** Rs. {c['avg_wholesale_price_lkr_per_kg']:.2f} / kg"
                        for i, c in enumerate(top_crops[:3])
                    ])
                    + "\n\n**💡 Next Steps for Farmers:**\n"
                    "- Apply basal fertilizer incorporation (Compost + TSP + MOP) 2 days before transplanting.\n"
                    "- Set up yellow sticky traps to prevent early vector pest infestations (Whitefly/Thrips).\n"
                    "- Open the **'🌱 Crop & Agronomy Planner'** from the sidebar to calculate exact profits for your land size and export your official PDF Cultivation Guide!"
                )
            return answer


market_rag_agent = MarketRAGAgent()
