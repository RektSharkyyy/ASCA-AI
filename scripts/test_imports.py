import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from src.infrastructure.config import config
from src.infrastructure.logging import logger
from src.infrastructure.db import init_db
from src.agents.guardrail import MarketInsight, RiskLevel
from src.agents.market_scout import market_scout_agent
from src.agents.matcher import matcher_agent

async def main():
    logger.info("Testing Market Scout Agent + Demand Supply Matcher Agent Pipeline...")
    await init_db()
    
    # 1. Market Scout Parallel Analysis
    logger.info("Step 1: Running MarketScoutAgent async parallel crop analysis...")
    insights = await market_scout_agent.scout_market_parallel_async(
        center_id="DAMBULLA",
        crops=["tomato", "carrot", "beans", "eggplant"]
    )
    
    # Force an anomaly for testing matcher if synthetic didn't trigger
    if insights:
        insights[0].surplus_anomaly_detected = True
        insights[0].risk_level = RiskLevel.HIGH
        insights[0].predicted_wholesale_price_lkr = insights[0].current_wholesale_price_lkr * 0.5
    
    # 2. Demand Supply Matcher Analysis
    logger.info("Step 2: Running DemandSupplyMatcherAgent ChromaDB + FEFO matching...")
    matches = await matcher_agent.match_surplus_crops_async(insights)
    
    logger.info(f"Matcher Agent returned {len(matches)} B2B Matches:")
    for match in matches:
        logger.info(f" - Buyer: {match.company_name:<30} | Crop: {match.crop_name:<10} | Volume: {match.matched_volume_tons:<5} T | FEFO Score: {match.fefo_risk_score}")

if __name__ == "__main__":
    asyncio.run(main())
