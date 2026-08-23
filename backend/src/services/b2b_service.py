"""
B2B matching service.

Bridges the Market Scout (surplus detection) and the Demand-Supply Matcher
(ChromaDB + FEFO risk engine) into the HTTP DTOs used by the B2B directory view.
"""

import asyncio
from typing import List, Optional

from src.agents.market_scout import market_scout_agent
from src.agents.matcher import matcher_agent
from src.agents.tools.matcher_tool import CENTER_HUB_DISTANCES_KM, chroma_b2b_store
from src.api.schemas import (
    B2BBuyerOut,
    B2BBuyersResponse,
    B2BMatchOut,
    B2BMatchResponse,
)
from src.infrastructure.logging import logger
from src.services.crop_catalog import (
    DEFAULT_CROP_BASKET,
    crop_label,
    normalise_centre,
    normalise_crop,
)


class B2BService:
    """Read + match facade over the B2B buyer registry."""

    async def list_buyers(self, centre_id: str) -> B2BBuyersResponse:
        """Buyer directory, annotated with distance from the active centre."""
        centre = normalise_centre(centre_id)
        raw_buyers = await asyncio.to_thread(chroma_b2b_store.list_all_buyers)
        distances = CENTER_HUB_DISTANCES_KM.get(centre, {})

        buyers: List[B2BBuyerOut] = []
        for buyer in raw_buyers:
            crops = [normalise_crop(c) for c in buyer.get("preferred_crops", [])]
            buyers.append(
                B2BBuyerOut(
                    buyer_code=buyer["buyer_code"],
                    company_name=buyer["company_name"],
                    buyer_type=buyer["buyer_type"],
                    location=buyer["location"],
                    daily_capacity_tons=round(float(buyer["daily_capacity_tons"]), 2),
                    preferred_crops=crops,
                    preferred_crop_labels=[crop_label(c) for c in crops],
                    distance_km=distances.get(buyer["location"]),
                )
            )

        return B2BBuyersResponse(centre_id=centre, total=len(buyers), buyers=buyers)

    async def match_surplus(
        self, centre_id: str, crops: Optional[List[str]] = None
    ) -> B2BMatchResponse:
        """
        Scouts the crop basket, then FEFO-ranks buyers for every surplus anomaly.

        Returns an empty match list (not an error) when no anomalies are found -
        that is a valid, healthy market state the UI renders as "no action needed".
        """
        centre = normalise_centre(centre_id)
        basket = [normalise_crop(c) for c in (crops or DEFAULT_CROP_BASKET)]

        insights = await market_scout_agent.scout_market_parallel_async(centre, basket)
        anomaly_count = sum(1 for i in insights if i.surplus_anomaly_detected)

        matches = await matcher_agent.match_surplus_crops_async(insights)
        logger.info(f"B2BService produced {len(matches)} matches for {centre}")

        out = [
            B2BMatchOut(
                buyer_code=m.buyer_code,
                company_name=m.company_name,
                crop_name=m.crop_name,
                crop_label=crop_label(m.crop_name),
                matched_volume_tons=round(float(m.matched_volume_tons), 2),
                fefo_risk_score=float(m.fefo_risk_score),
                recommended_action=m.recommended_action,
            )
            for m in matches
        ]

        total_volume = round(sum(m.matched_volume_tons for m in out), 2)
        avg_fefo = round(sum(m.fefo_risk_score for m in out) / len(out), 2) if out else 0.0

        return B2BMatchResponse(
            centre_id=centre,
            anomaly_count=anomaly_count,
            total_volume_tons=total_volume,
            average_fefo_score=avg_fefo,
            matches=out,
        )


b2b_service = B2BService()
