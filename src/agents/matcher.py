import asyncio
from typing import List, Dict, Any, Optional
from src.infrastructure.logging import logger
from src.agents.guardrail import MarketInsight, B2BMatchRecommendation
from src.agents.tools.matcher_tool import chroma_b2b_store, FEFORiskEngine

class DemandSupplyMatcherAgent:
    """
    Demand-Supply Matcher Agent (The B2B Negotiator):
    Matches market surpluses with processing factories/buyers using FEFO Risk Engine
    and dynamic volume pool allocation.
    """

    def __init__(self, max_concurrent_searches: int = 5):
        # Concurrency limiter to protect Vector DB disk I/O
        self._semaphore = asyncio.Semaphore(max_concurrent_searches)

    async def match_single_insight_async(self, insight: MarketInsight) -> List[B2BMatchRecommendation]:
        """Matches a single surplus market insight with available B2B buyers safely."""
        if not insight.surplus_anomaly_detected and insight.risk_level.value not in ["HIGH", "CRITICAL"]:
            return []

        crop_name = insight.crop_name
        center_id = insight.center_id
        surplus_volume = insight.supply_volume_tons

        logger.info(f"DemandSupplyMatcherAgent finding B2B buyers for {crop_name} surplus at {center_id} ({surplus_volume} Tons)...")

        async with self._semaphore:
            # Query ChromaDB in a worker thread to keep the event loop responsive
            candidate_buyers = await asyncio.to_thread(
                chroma_b2b_store.search_buyers_for_crop,
                crop_name,
                3
            )

        if not candidate_buyers:
            logger.warning(f"⚠️ No matching B2B buyers found for {crop_name} (Center: {center_id}).")
            return []

        recommendations = []
        remaining_surplus = surplus_volume

        for buyer in candidate_buyers:
            if remaining_surplus <= 0:
                break  # Stop allocating once surplus volume is fully matched

            buyer_capacity = buyer.get("daily_capacity_tons", 0.0)
            if buyer_capacity <= 0:
                continue

            allocated_volume = min(remaining_surplus, buyer_capacity)

            fefo_score = FEFORiskEngine.calculate_risk_score(
                crop_name=crop_name,
                center_id=center_id,
                buyer_location=buyer["location"],
                surplus_volume_tons=allocated_volume,
                buyer_capacity_tons=buyer_capacity
            )

            action_text = (
                f"Route {allocated_volume:.1f} tons of excess {crop_name} from {center_id} "
                f"to {buyer['company_name']} ({buyer['location']}). FEFO Risk Score: {fefo_score:.2f}."
            )

            rec = B2BMatchRecommendation(
                buyer_code=buyer["buyer_code"],
                company_name=buyer["company_name"],
                crop_name=crop_name,
                matched_volume_tons=allocated_volume,
                fefo_risk_score=fefo_score,
                recommended_action=action_text
            )
            recommendations.append(rec)
            
            # Deduct allocated volume from surplus pool
            remaining_surplus -= allocated_volume

        # Sort: Primary by FEFO score (ascending), Secondary by Matched Volume (descending)
        recommendations.sort(key=lambda x: (x.fefo_risk_score, -x.matched_volume_tons))
        return recommendations

    async def match_surplus_crops_async(self, insights: List[MarketInsight]) -> List[B2BMatchRecommendation]:
        """Concurrently matches multiple surplus insights using asyncio.gather()."""
        surplus_insights = [
            i for i in insights 
            if i.surplus_anomaly_detected or i.risk_level.value in ["HIGH", "CRITICAL"]
        ]
        if not surplus_insights:
            logger.info("DemandSupplyMatcherAgent: No surplus anomalies detected to match.")
            return []

        logger.info(f"DemandSupplyMatcherAgent matching {len(surplus_insights)} surplus anomalies concurrently...")
        tasks = [self.match_single_insight_async(insight) for insight in surplus_insights]
        results_nested = await asyncio.gather(*tasks)

        # Flatten list of lists
        all_matches = [match for sublist in results_nested for match in sublist]
        logger.info(f"DemandSupplyMatcherAgent generated {len(all_matches)} total B2B Match Recommendations.")
        return all_matches

matcher_agent = DemandSupplyMatcherAgent()

