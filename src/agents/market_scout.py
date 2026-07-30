import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.logging import logger
from src.infrastructure.config import config
from src.infrastructure.db import AsyncSessionLocal
from src.infrastructure.models import MarketDataModel
from src.agents.guardrail import MarketInsight, RiskLevel
from src.agents.tools.forecasting_tool import forecast_engine

class MarketScoutAgent:
    """
    Market Scout Agent (The Forecaster):
    Monitors wholesale market price trends & supply volumes in Dambulla and Thambuththegama.
    Uses Prophet & Time-Series Models via parallel async tasks to predict 14-day price drops
    and detect surplus anomalies with DB pool concurrency control.
    """

    def __init__(self):
        self.centers = [c["id"] for c in config.params.get("economic_centers", [])]

    async def fetch_historical_data_async(
        self,
        center_id: str,
        crop_name: str,
        days_back: int = 60
    ) -> pd.DataFrame:
        """Fetches historical price & supply data using a clean, isolated database session."""
        async with AsyncSessionLocal() as session:
            try:
                # Use timezone-naive datetime for DB query compatibility
                start_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_back)
                stmt = select(MarketDataModel).where(
                    MarketDataModel.center_id == center_id,
                    MarketDataModel.crop_name == crop_name,
                    MarketDataModel.date >= start_date
                ).order_by(MarketDataModel.date.asc())

                result = await session.execute(stmt)
                records = result.scalars().all()

                if records and len(records) >= 14:
                    data = [
                        {
                            "ds": r.date,
                            "y": r.wholesale_price_lkr,
                            "supply_tons": r.supply_volume_tons
                        }
                        for r in records
                    ]
                    return pd.DataFrame(data)
                
                logger.warning(f"Insufficient DB records for {crop_name} at {center_id}. Using synthetic data.")
                return self._generate_synthetic_market_series(crop_name, days_back)

            except Exception as e:
                logger.error(f"Error fetching DB market data for {crop_name} at {center_id}: {str(e)}")
                return self._generate_synthetic_market_series(crop_name, days_back)

    def _generate_synthetic_market_series(self, crop_name: str, days_back: int) -> pd.DataFrame:
        """Generates realistic daily price and supply time-series for Sri Lankan crops."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        dates = [now - timedelta(days=i) for i in range(days_back, -1, -1)]
        base_prices = {
            "tomato": 240.0, "carrot": 320.0, "beans": 280.0,
            "eggplant": 190.0, "cabbage": 160.0, "green_chilli": 450.0
        }
        base_price = base_prices.get(crop_name.lower(), 200.0)

        trend = np.linspace(base_price * 1.1, base_price * 0.75, len(dates))
        noise = np.random.normal(0, 8.0, len(dates))
        prices = np.clip(trend + noise, a_min=30.0, a_max=None)
        supplies = np.clip(np.linspace(15.0, 55.0, len(dates)) + np.random.normal(0, 3.0, len(dates)), a_min=5.0, a_max=None)

        data = [
            {"ds": d, "y": round(float(p), 2), "supply_tons": round(float(s), 2)}
            for d, p, s in zip(dates, prices, supplies)
        ]
        return pd.DataFrame(data)

    async def analyze_crop_async(
        self,
        center_id: str,
        crop_name: str
    ) -> MarketInsight:
        """Fetches data and runs 14-day forecast safely without blocking the event loop."""
        df = await self.fetch_historical_data_async(center_id, crop_name)
        
        # CPU-Bound Model Offloading to prevent blocking the async event loop
        forecast_res = await forecast_engine.forecast_crop_prices_async(df, center_id, crop_name)

        return MarketInsight(
            center_id=forecast_res["center_id"],
            crop_name=forecast_res["crop_name"],
            current_wholesale_price_lkr=forecast_res["current_wholesale_price_lkr"],
            predicted_wholesale_price_lkr=forecast_res["predicted_wholesale_price_lkr"],
            supply_volume_tons=forecast_res["supply_volume_tons"],
            surplus_anomaly_detected=forecast_res["surplus_anomaly_detected"],
            risk_level=RiskLevel(forecast_res["risk_level"])
        )

    async def scout_market_parallel_async(
        self,
        center_id: str,
        crops: Optional[List[str]] = None
    ) -> List[MarketInsight]:
        """Scouts multiple crops concurrently with dynamic semaphore safety."""
        target_crops = crops or ["tomato", "carrot", "beans", "eggplant", "cabbage", "green_chilli"]
        logger.info(f"MarketScoutAgent scouting {len(target_crops)} crops concurrently for {center_id}...")

        # Concurrency limit to prevent DB connection pool exhaustion
        semaphore = asyncio.Semaphore(4)

        async def bounded_scout(crop_name: str):
            async with semaphore:
                return await self.analyze_crop_async(center_id, crop_name)

        tasks = [bounded_scout(crop) for crop in target_crops]
        insights = await asyncio.gather(*tasks)

        anomaly_count = sum(1 for i in insights if i.surplus_anomaly_detected)
        logger.info(f"MarketScoutAgent completed scouting for {center_id}: Detected {anomaly_count} surplus anomalies.")
        return list(insights)

market_scout_agent = MarketScoutAgent()
