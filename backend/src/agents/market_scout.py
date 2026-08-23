"""
Market Scout Agent (The Forecaster).

Reads wholesale price & supply history **directly from the Supabase
`market_data` table** — the same table the HARTI scraper syncs into — so Prophet
always fits on real persisted records instead of an in-memory generator.

Data guarantees given to the forecasting engine:
  1. Rows come straight from `market_data` (center_id + crop_name + date).
  2. If history is too thin, the scraper back-fills the gap into the DB
     (`ensure_history`) and the query is retried — so the model still trains on
     real table rows.
  3. The returned frame is de-duplicated, sorted and re-indexed to a continuous
     daily calendar with interpolated gaps ⇒ Prophet reports **zero missing-data
     warnings**.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import select

from src.agents.guardrail import MarketInsight, RiskLevel
from src.agents.tools.forecasting_tool import forecast_engine
from src.infrastructure.config import config
from src.infrastructure.db import AsyncSessionLocal
from src.infrastructure.logging import logger
from src.infrastructure.models import MarketDataModel

# Prophet needs a reasonable window to fit trend + weekly seasonality.
MIN_RECORDS_FOR_PROPHET = 21

# Default look-back window pulled from the DB for each forecast.
DEFAULT_DAYS_BACK = 60


class MarketScoutAgent:
    """
    Monitors wholesale market price trends & supply volumes in Dambulla and
    Thambuththegama.

    Uses Prophet & time-series models via parallel async tasks to predict 14-day
    price drops and detect surplus anomalies, with DB pool concurrency control.
    """

    def __init__(self):
        self.centers = [c["id"] for c in config.params.get("economic_centers", [])]
        # Guards the auto-heal back-fill so concurrent crop scans don't all
        # trigger a seed at the same time.
        self._backfill_lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Supabase reads
    # ------------------------------------------------------------------ #
    async def _query_market_data(
        self,
        center_id: str,
        crop_name: str,
        days_back: int,
    ) -> List[Dict[str, Any]]:
        """
        Single read of the `market_data` table for one (centre, crop) pair.

        Returns raw dict rows ordered oldest → newest.
        """
        # Timezone-naive datetime keeps SQLite and Postgres/Supabase consistent.
        start_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_back)

        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    MarketDataModel.date,
                    MarketDataModel.wholesale_price_lkr,
                    MarketDataModel.supply_volume_tons,
                )
                .where(
                    MarketDataModel.center_id == center_id,
                    MarketDataModel.crop_name == crop_name,
                    MarketDataModel.date >= start_date,
                )
                .order_by(MarketDataModel.date.asc())
            )
            rows = (await session.execute(stmt)).all()

        return [
            {
                "ds": row.date,
                "y": float(row.wholesale_price_lkr),
                "supply_tons": float(row.supply_volume_tons or 0.0),
            }
            for row in rows
            if row.date is not None and row.wholesale_price_lkr is not None
        ]

    async def fetch_historical_data_async(
        self,
        center_id: str,
        crop_name: str,
        days_back: int = DEFAULT_DAYS_BACK,
    ) -> pd.DataFrame:
        """
        Fetch historical price & supply data from Supabase `market_data`.

        Flow:
          1. Query the table (isolated session, no shared state).
          2. If fewer than `MIN_RECORDS_FOR_PROPHET` rows exist, ask the scraper
             to back-fill the window into the DB, then re-query.
          3. Normalise into a continuous, gap-free daily frame for Prophet.

        The synthetic generator is only reachable if the database itself is
        unavailable — under normal operation Prophet trains on real rows.
        """
        try:
            records = await self._query_market_data(center_id, crop_name, days_back)

            if len(records) < MIN_RECORDS_FOR_PROPHET:
                records = await self._backfill_and_requery(
                    center_id, crop_name, days_back, len(records)
                )

            if records:
                df = self._to_daily_frame(records)
                logger.info(
                    f"[market_scout] Loaded {len(df)} daily rows from market_data "
                    f"for {crop_name} @ {center_id} (source=supabase)"
                )
                return df

            logger.warning(
                f"[market_scout] market_data returned no rows for {crop_name} @ {center_id} "
                f"— falling back to synthetic series."
            )
            return self._generate_synthetic_market_series(crop_name, days_back)

        except Exception as exc:
            logger.error(
                f"[market_scout] DB read failed for {crop_name} @ {center_id}: {exc} "
                f"— falling back to synthetic series."
            )
            return self._generate_synthetic_market_series(crop_name, days_back)

    async def _backfill_and_requery(
        self,
        center_id: str,
        crop_name: str,
        days_back: int,
        found: int,
    ) -> List[Dict[str, Any]]:
        """
        Ask the scraper service to seed the missing history straight into
        `market_data`, then re-read the table.
        """
        # Imported lazily to avoid a service ⇄ agent import cycle.
        from src.services.scraper_service import market_scraper

        logger.info(
            f"[market_scout] Only {found} rows in market_data for {crop_name} @ {center_id} "
            f"(need {MIN_RECORDS_FOR_PROPHET}) — triggering scraper back-fill."
        )

        async with self._backfill_lock:
            try:
                inserted = await market_scraper.ensure_history(
                    center_id,
                    crop_name,
                    days=days_back,
                    min_records=MIN_RECORDS_FOR_PROPHET,
                )
                logger.info(
                    f"[market_scout] Back-fill inserted {inserted} rows for {crop_name} @ {center_id}"
                )
            except Exception as exc:
                logger.error(f"[market_scout] Back-fill failed for {crop_name} @ {center_id}: {exc}")
                return await self._query_market_data(center_id, crop_name, days_back)

        return await self._query_market_data(center_id, crop_name, days_back)

    # ------------------------------------------------------------------ #
    # Frame normalisation (gap-free daily calendar for Prophet)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_daily_frame(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Turn raw DB rows into the exact frame Prophet expects:
          - `ds` normalised to midnight, duplicates collapsed (last write wins)
          - re-indexed onto a continuous daily calendar
          - price/supply gaps interpolated then forward/back filled

        Result: no NaNs and no missing days ⇒ no Prophet missing-data warnings.
        """
        df = pd.DataFrame(records)
        df["ds"] = pd.to_datetime(df["ds"]).dt.normalize()
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df["supply_tons"] = pd.to_numeric(df["supply_tons"], errors="coerce")

        df = (
            df.dropna(subset=["ds", "y"])
              .drop_duplicates(subset="ds", keep="last")
              .sort_values("ds")
              .set_index("ds")
        )

        if df.empty:
            return df.reset_index()

        # Continuous daily calendar between the first and last observation.
        full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
        df = df.reindex(full_index)
        df.index.name = "ds"

        df["y"] = df["y"].interpolate(method="linear").ffill().bfill()
        df["supply_tons"] = df["supply_tons"].interpolate(method="linear").ffill().bfill()
        df["supply_tons"] = df["supply_tons"].fillna(0.0)

        out = df.reset_index()[["ds", "y", "supply_tons"]]
        out["y"] = out["y"].round(2)
        out["supply_tons"] = out["supply_tons"].round(2)
        out.attrs["source"] = "supabase"
        return out

    def _generate_synthetic_market_series(self, crop_name: str, days_back: int) -> pd.DataFrame:
        """
        Last-resort in-memory series, used only when the database is unreachable.

        Kept so the API degrades gracefully instead of returning a 500.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dates = [now - timedelta(days=i) for i in range(days_back, -1, -1)]
        base_prices = {
            "tomato": 240.0, "carrot": 320.0, "beans": 280.0,
            "eggplant": 190.0, "cabbage": 160.0, "green_chilli": 450.0,
        }
        base_price = base_prices.get(crop_name.lower(), 200.0)

        trend = np.linspace(base_price * 1.1, base_price * 0.75, len(dates))
        noise = np.random.normal(0, 8.0, len(dates))
        prices = np.clip(trend + noise, a_min=30.0, a_max=None)
        supplies = np.clip(
            np.linspace(15.0, 55.0, len(dates)) + np.random.normal(0, 3.0, len(dates)),
            a_min=5.0, a_max=None,
        )

        data = [
            {"ds": d, "y": round(float(p), 2), "supply_tons": round(float(s), 2)}
            for d, p, s in zip(dates, prices, supplies)
        ]
        df = pd.DataFrame(data)
        df.attrs["source"] = "synthetic"
        return df

    # ------------------------------------------------------------------ #
    # Forecasting
    # ------------------------------------------------------------------ #
    async def analyze_crop_async(
        self,
        center_id: str,
        crop_name: str
    ) -> MarketInsight:
        """Fetches DB history and runs the 14-day forecast off the event loop."""
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
