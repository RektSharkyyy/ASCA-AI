import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from prophet import Prophet
from src.infrastructure.logging import logger
from src.infrastructure.config import config

class MarketForecastEngine:
    """
    Time-Series Forecasting Engine using Prophet and statistical trend models
    for 14-day vegetable price predictions and surplus anomaly detection.
    """
    
    def __init__(self, horizon_days: int = 14):
        self.horizon_days = horizon_days
        self.anomaly_threshold_pct = config.params.get("forecasting", {}).get("surplus_anomaly_threshold_percentage", 25.0)

    def forecast_crop_prices_sync(
        self,
        historical_df: pd.DataFrame,
        center_id: str,
        crop_name: str
    ) -> Dict[str, Any]:
        """
        Runs Prophet forecasting model on historical daily market data.
        DataFrame must contain columns: ['ds' (date), 'y' (wholesale_price_lkr), 'supply_tons']
        """
        if historical_df.empty or len(historical_df) < 7:
            logger.warning(f"Insufficient historical data ({len(historical_df)} rows) for {crop_name} at {center_id}. Using statistical fallback.")
            return self._statistical_fallback(historical_df, center_id, crop_name)

        try:
            # Prepare Prophet dataframe
            df = historical_df[['ds', 'y']].copy()
            df['ds'] = pd.to_datetime(df['ds'])
            df['y'] = pd.to_numeric(df['y'], errors='coerce')
            df = df.dropna().sort_values('ds')

            # Fit Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05
            )
            model.fit(df)

            # Make 14-day future dataframe
            future = model.make_future_dataframe(periods=self.horizon_days)
            forecast = model.predict(future)

            current_price = float(df['y'].iloc[-1])
            latest_supply = float(historical_df['supply_tons'].iloc[-1]) if 'supply_tons' in historical_df.columns else 10.0

            # Get predicted price at the end of horizon
            future_forecast = forecast.tail(self.horizon_days)
            predicted_price = float(np.clip(future_forecast['yhat'].mean(), a_min=10.0, a_max=None))

            # Compute percentage price change
            price_change_pct = ((current_price - predicted_price) / current_price) * 100.0 if current_price > 0 else 0.0
            is_anomaly = price_change_pct >= self.anomaly_threshold_pct

            # Determine risk level
            if price_change_pct >= 40.0:
                risk_level = "CRITICAL"
            elif price_change_pct >= 25.0:
                risk_level = "HIGH"
            elif price_change_pct >= 10.0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            return {
                "center_id": center_id,
                "crop_name": crop_name,
                "current_wholesale_price_lkr": round(current_price, 2),
                "predicted_wholesale_price_lkr": round(predicted_price, 2),
                "supply_volume_tons": round(latest_supply, 2),
                "price_change_pct": round(price_change_pct, 2),
                "surplus_anomaly_detected": is_anomaly,
                "risk_level": risk_level,
                "model_used": "prophet"
            }

        except Exception as e:
            logger.error(f"Prophet forecast failed for {crop_name} at {center_id}: {str(e)}. Triggering fallback.")
            return self._statistical_fallback(historical_df, center_id, crop_name)

    def _statistical_fallback(
        self,
        historical_df: pd.DataFrame,
        center_id: str,
        crop_name: str
    ) -> Dict[str, Any]:
        """Statistical moving average trend fallback if Prophet is missing data."""
        if not historical_df.empty and 'y' in historical_df.columns:
            current_price = float(historical_df['y'].iloc[-1])
            avg_price = float(historical_df['y'].mean())
            supply = float(historical_df['supply_tons'].iloc[-1]) if 'supply_tons' in historical_df.columns else 20.0
        else:
            current_price = 200.0
            avg_price = 180.0
            supply = 25.0

        # Simple trend estimation
        predicted_price = round(avg_price * 0.85, 2) # Assume slight seasonal decline
        price_change_pct = ((current_price - predicted_price) / current_price) * 100.0 if current_price > 0 else 0.0
        is_anomaly = price_change_pct >= self.anomaly_threshold_pct

        return {
            "center_id": center_id,
            "crop_name": crop_name,
            "current_wholesale_price_lkr": current_price,
            "predicted_wholesale_price_lkr": predicted_price,
            "supply_volume_tons": supply,
            "price_change_pct": round(price_change_pct, 2),
            "surplus_anomaly_detected": is_anomaly,
            "risk_level": "HIGH" if is_anomaly else "LOW",
            "model_used": "statistical_fallback"
        }

    async def forecast_crop_prices_async(
        self,
        historical_df: pd.DataFrame,
        center_id: str,
        crop_name: str
    ) -> Dict[str, Any]:
        """Asynchronously executes CPU-bound Prophet forecasting in a separate worker thread."""
        return await asyncio.to_thread(
            self.forecast_crop_prices_sync,
            historical_df,
            center_id,
            crop_name
        )

    # ------------------------------------------------------------------ #
    # Chart-ready curve (single model fit, reused by the HTTP API)
    # ------------------------------------------------------------------ #
    def forecast_curve_sync(
        self,
        historical_df: pd.DataFrame,
        center_id: str,
        crop_name: str,
        history_days: int = 8
    ) -> Dict[str, Any]:
        """
        Returns the standard forecast summary PLUS a day-by-day curve for charting.

        Runs Prophet only ONCE, then derives both the summary metrics and the
        historical/forecast series so the API never pays for a second model fit.

        Curve contract:
            - `history`: last `history_days` observed prices (oldest -> newest)
            - `forecast`: next `horizon_days` predicted prices with uncertainty bands
        """
        summary = self.forecast_crop_prices_sync(historical_df, center_id, crop_name)
        history: List[Dict[str, Any]] = []
        forecast_points: List[Dict[str, Any]] = []

        try:
            df = historical_df[['ds', 'y']].copy()
            df['ds'] = pd.to_datetime(df['ds'])
            df['y'] = pd.to_numeric(df['y'], errors='coerce')
            df = df.dropna().sort_values('ds')

            for _, row in df.tail(max(1, history_days)).iterrows():
                history.append({
                    "date": row['ds'].to_pydatetime(),
                    "price": round(float(row['y']), 2),
                })

            if len(df) >= 7:
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05
                )
                model.fit(df)
                future = model.make_future_dataframe(periods=self.horizon_days)
                forecast = model.predict(future).tail(self.horizon_days)

                for _, row in forecast.iterrows():
                    yhat = float(np.clip(row['yhat'], a_min=10.0, a_max=None))
                    forecast_points.append({
                        "date": pd.to_datetime(row['ds']).to_pydatetime(),
                        "price": round(yhat, 2),
                        "lower": round(float(np.clip(row.get('yhat_lower', yhat * 0.9), a_min=5.0, a_max=None)), 2),
                        "upper": round(float(max(row.get('yhat_upper', yhat * 1.1), yhat)), 2),
                    })

        except Exception as e:
            logger.error(f"Forecast curve generation failed for {crop_name} at {center_id}: {str(e)}")

        if not forecast_points:
            forecast_points = self._linear_curve_fallback(summary, history)

        return {**summary, "history": history, "forecast": forecast_points}

    def _linear_curve_fallback(
        self,
        summary: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Straight-line interpolation between current and predicted price."""
        current = float(summary.get("current_wholesale_price_lkr", 200.0))
        target = float(summary.get("predicted_wholesale_price_lkr", current))
        last_date = history[-1]["date"] if history else datetime.now()

        points: List[Dict[str, Any]] = []
        for step in range(1, self.horizon_days + 1):
            price = current + (target - current) * (step / self.horizon_days)
            points.append({
                "date": last_date + timedelta(days=step),
                "price": round(price, 2),
                "lower": round(price * 0.9, 2),
                "upper": round(price * 1.1, 2),
            })
        return points

    async def forecast_curve_async(
        self,
        historical_df: pd.DataFrame,
        center_id: str,
        crop_name: str,
        history_days: int = 8
    ) -> Dict[str, Any]:
        """Async wrapper: keeps the event loop free while Prophet fits the model."""
        return await asyncio.to_thread(
            self.forecast_curve_sync,
            historical_df,
            center_id,
            crop_name,
            history_days
        )

forecast_engine = MarketForecastEngine()

