"""
Market analytics service.

Adapts the Market Scout agent + Prophet forecast engine into the HTTP DTOs the
frontend charts consume. All heavy work stays async so FastAPI keeps serving
other requests while Prophet fits models in worker threads.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.market_scout import market_scout_agent
from src.agents.tools.forecasting_tool import forecast_engine
from src.api.schemas import (
    ForecastPoint,
    MarketForecastResponse,
    MarketInsightOut,
    MarketInsightsResponse,
)
from src.infrastructure.logging import logger
from src.services.crop_catalog import (
    DEFAULT_CROP_BASKET,
    crop_label,
    forecast_horizon_days,
    normalise_centre,
    normalise_crop,
)


def _label_date(value: Any) -> str:
    """Formats a date as the '14 Aug' label the Recharts X-axis expects."""
    if isinstance(value, datetime):
        return value.strftime("%d %b")
    return str(value)


def _build_series(curve: Dict[str, Any]) -> List[ForecastPoint]:
    """
    Merges history + forecast into one continuous chart series.

    The final historical point is duplicated as the first forecast point so the
    'actual' and 'forecast' lines visually connect instead of showing a gap.
    """
    history = curve.get("history", []) or []
    forecast = curve.get("forecast", []) or []
    series: List[ForecastPoint] = []

    for point in history:
        series.append(ForecastPoint(date=_label_date(point.get("date")), actual=point.get("price")))

    # Bridge the two lines at "today".
    if series and forecast:
        last = series[-1]
        last.forecast = last.actual
        last.lower = last.actual
        last.upper = last.actual

    for point in forecast:
        series.append(
            ForecastPoint(
                date=_label_date(point.get("date")),
                forecast=point.get("price"),
                lower=point.get("lower"),
                upper=point.get("upper"),
            )
        )

    return series


def _pick_horizon_price(forecast: List[Dict[str, Any]], day: int, fallback: float) -> float:
    """Returns the forecast price for `day` (1-indexed), clamped to the series length."""
    if not forecast:
        return round(fallback, 2)
    index = min(max(day, 1), len(forecast)) - 1
    return round(float(forecast[index].get("price", fallback)), 2)


class MarketService:
    """Read-oriented facade over the Market Scout agent for the HTTP layer."""

    def __init__(self, history_days: int = 8):
        self.history_days = history_days

    async def get_forecast(self, centre_id: str, crop: str) -> MarketForecastResponse:
        """Full 14-day price curve + summary metrics for a single crop."""
        centre = normalise_centre(centre_id)
        crop_name = normalise_crop(crop)

        logger.info(f"MarketService building forecast curve for {crop_name} at {centre}")

        history_df = await market_scout_agent.fetch_historical_data_async(centre, crop_name)
        curve = await forecast_engine.forecast_curve_async(
            history_df, centre, crop_name, history_days=self.history_days
        )

        forecast_points = curve.get("forecast", []) or []
        current_price = float(curve.get("current_wholesale_price_lkr", 0.0))
        mean_forecast = float(curve.get("predicted_wholesale_price_lkr", current_price))

        day7 = _pick_horizon_price(forecast_points, 7, mean_forecast)
        day14 = _pick_horizon_price(forecast_points, len(forecast_points) or 14, mean_forecast)

        # Frontend convention: negative percentage == projected price drop.
        price_change_pct = 0.0
        if current_price > 0:
            price_change_pct = round(((day14 - current_price) / current_price) * 100.0, 2)

        return MarketForecastResponse(
            centre_id=centre,
            crop_name=crop_name,
            crop_label=crop_label(crop_name),
            current_price_lkr=round(current_price, 2),
            day7_price_lkr=day7,
            day14_price_lkr=day14,
            mean_forecast_price_lkr=round(mean_forecast, 2),
            price_change_pct=price_change_pct,
            supply_volume_tons=round(float(curve.get("supply_volume_tons", 0.0)), 2),
            surplus_anomaly_detected=bool(curve.get("surplus_anomaly_detected", False)),
            risk_level=str(curve.get("risk_level", "LOW")),
            model_used=str(curve.get("model_used", "prophet")),
            horizon_days=forecast_horizon_days(),
            series=_build_series(curve),
        )

    async def get_insights(
        self, centre_id: str, crops: Optional[List[str]] = None
    ) -> MarketInsightsResponse:
        """Parallel scout across the crop basket; powers the analytics summary grid."""
        centre = normalise_centre(centre_id)
        basket = [normalise_crop(c) for c in (crops or DEFAULT_CROP_BASKET)]

        insights = await market_scout_agent.scout_market_parallel_async(centre, basket)

        out: List[MarketInsightOut] = []
        for insight in insights:
            current = float(insight.current_wholesale_price_lkr)
            predicted = float(insight.predicted_wholesale_price_lkr)
            change_pct = round(((predicted - current) / current) * 100.0, 2) if current > 0 else 0.0

            out.append(
                MarketInsightOut(
                    centre_id=insight.center_id,
                    crop_name=insight.crop_name,
                    crop_label=crop_label(insight.crop_name),
                    current_price_lkr=round(current, 2),
                    predicted_price_lkr=round(predicted, 2),
                    price_change_pct=change_pct,
                    supply_volume_tons=round(float(insight.supply_volume_tons), 2),
                    surplus_anomaly_detected=bool(insight.surplus_anomaly_detected),
                    risk_level=insight.risk_level.value,
                )
            )

        return MarketInsightsResponse(
            centre_id=centre,
            anomaly_count=sum(1 for i in out if i.surplus_anomaly_detected),
            insights=out,
        )


market_service = MarketService()
