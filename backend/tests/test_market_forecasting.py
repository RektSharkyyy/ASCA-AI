import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.agents.tools.forecasting_tool import forecast_engine
from src.agents.guardrail import MarketInsight, RiskLevel

def test_prophet_engine_execution():
    """Test Prophet forecasting engine runs on synthetic historical data."""
    # Generate 60 days of sample historical price series
    base_date = datetime.now() - timedelta(days=60)
    dates = [base_date + timedelta(days=i) for i in range(60)]
    prices = [100.0 + (i * 0.5) for i in range(60)]
    
    df = pd.DataFrame({"ds": dates, "y": prices, "supply_tons": [15.0]*60})
    
    result = forecast_engine.forecast_crop_prices_sync(
        historical_df=df,
        center_id="DAMBULLA",
        crop_name="tomato"
    )
    assert result is not None
    assert "predicted_wholesale_price_lkr" in result
    assert result["predicted_wholesale_price_lkr"] > 0
    assert "risk_level" in result
    assert result["model_used"] in ["prophet", "statistical_moving_average"]

def test_market_insight_guardrail_anomaly_detection():
    """Test Pydantic MarketInsight schema auto-flags severe price drop anomalies (>25%)."""
    insight = MarketInsight(
        center_id="DAMBULLA",
        crop_name="tomato",
        current_wholesale_price_lkr=120.0,
        predicted_wholesale_price_lkr=75.0, # 37.5% price collapse
        supply_volume_tons=45.0
    )
    
    assert insight.surplus_anomaly_detected is True
    assert insight.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

def test_market_insight_guardrail_stable_condition():
    """Test MarketInsight stays LOW risk when prices are stable."""
    insight = MarketInsight(
        center_id="DAMBULLA",
        crop_name="carrot",
        current_wholesale_price_lkr=110.0,
        predicted_wholesale_price_lkr=115.0, # slight increase
        supply_volume_tons=12.0
    )
    
    assert insight.surplus_anomaly_detected is False
    assert insight.risk_level == RiskLevel.LOW
