"""
HTTP API contracts (DTOs) for ASCA AI.

These schemas are the ONLY types the frontend consumes, which keeps the internal
agent models (`MarketInsight`, `B2BMatchRecommendation`, `PipelineResult`) free to
evolve without breaking the UI.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

RiskLevelStr = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RouteStr = Literal["direct", "web_search", "rag"]
ActionIcon = Literal["pdf", "sms", "chart", "ext"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Health / meta
# --------------------------------------------------------------------------- #
class HealthResponse(BaseModel):
    """Lightweight liveness probe consumed by the UI status chips."""

    status: Literal["ok", "degraded"] = "ok"
    app: str = "ASCA AI"
    version: str = "1.0.0"
    environment: str = "development"
    llm_provider: str = "openrouter"
    llm_configured: bool = False
    web_search_enabled: bool = False
    timestamp: datetime = Field(default_factory=_utcnow)


class EconomicCentre(BaseModel):
    id: str = Field(..., examples=["DAMBULLA"])
    name: str
    location: str
    short: str = Field(..., description="3-letter badge used in the UI")


class CropOption(BaseModel):
    id: str = Field(..., description="Internal snake_case crop key")
    label: str = Field(..., description="Human readable label")


class MetaResponse(BaseModel):
    """Bootstrap payload so the frontend never hardcodes domain constants."""

    centres: List[EconomicCentre]
    crops: List[CropOption]
    forecast_horizon_days: int = 14
    currency: str = "LKR"


# --------------------------------------------------------------------------- #
# Shared chat building blocks
# --------------------------------------------------------------------------- #
class ThoughtStep(BaseModel):
    """One line in the collapsible 'Agent Reasoning' log."""

    tool: str = Field(..., description="Tool/model name, e.g. 'Prophet Forecast'")
    detail: str = Field(..., description="What the tool did")


class InlineAction(BaseModel):
    """Suggested follow-up button rendered under an agent message."""

    label: str
    icon: ActionIcon = "ext"
    primary: bool = False
    prompt: Optional[str] = Field(
        default=None,
        description="Message to re-send when the button is clicked",
    )


class ForecastPoint(BaseModel):
    """Single day on the price curve. `actual` and `forecast` are mutually sparse."""

    date: str = Field(..., description="Display label, e.g. '14 Aug'")
    actual: Optional[float] = None
    forecast: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None


class ChartPayload(BaseModel):
    """Inline chart artifact attached to an agent message."""

    crop: str = Field(..., description="Display label, e.g. 'Tomato'")
    centre_id: str = "DAMBULLA"
    unit: str = "LKR/kg"
    data: List[ForecastPoint] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    centre_id: str = Field(default="DAMBULLA", description="Active economic centre")
    session_id: Optional[str] = Field(default=None, description="Client-generated conversation id")


class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    route: Optional[RouteStr] = None
    in_scope: bool = True
    short_circuited: bool = False
    search_performed: bool = False
    sources: List[str] = Field(default_factory=list)
    thoughts: List[ThoughtStep] = Field(default_factory=list)
    actions: List[InlineAction] = Field(default_factory=list)
    chart: Optional[ChartPayload] = None
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=_utcnow)


class ChatHistoryItem(BaseModel):
    """A single saved message pair (query + answer) in a session."""
    id: int
    session_id: str
    query: str
    answer: str
    route: Optional[str] = None
    in_scope: bool = True
    centre_id: Optional[str] = None
    chart_data: Optional[str] = None   # raw JSON string
    latency_ms: Optional[int] = None
    created_at: datetime


class ChatSessionSummary(BaseModel):
    """Summary card shown in the history sidebar (one per session)."""
    session_id: str
    title: str                 # derived from first query
    message_count: int
    centre_id: Optional[str] = None
    last_message_at: datetime


# --------------------------------------------------------------------------- #
# Market analytics
# --------------------------------------------------------------------------- #
class MarketForecastResponse(BaseModel):
    centre_id: str
    crop_name: str = Field(..., description="Internal snake_case key")
    crop_label: str
    current_price_lkr: float
    day7_price_lkr: float
    day14_price_lkr: float
    mean_forecast_price_lkr: float
    price_change_pct: float = Field(..., description="Negative means a projected price drop")
    supply_volume_tons: float
    surplus_anomaly_detected: bool = False
    risk_level: RiskLevelStr = "LOW"
    model_used: str = "prophet"
    horizon_days: int = 14
    series: List[ForecastPoint] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)


class MarketInsightOut(BaseModel):
    centre_id: str
    crop_name: str
    crop_label: str
    current_price_lkr: float
    predicted_price_lkr: float
    price_change_pct: float
    supply_volume_tons: float
    surplus_anomaly_detected: bool = False
    risk_level: RiskLevelStr = "LOW"


class MarketInsightsResponse(BaseModel):
    centre_id: str
    anomaly_count: int = 0
    insights: List[MarketInsightOut] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# B2B matching
# --------------------------------------------------------------------------- #
class B2BBuyerOut(BaseModel):
    buyer_code: str
    company_name: str
    buyer_type: str
    location: str
    daily_capacity_tons: float
    preferred_crops: List[str] = Field(default_factory=list)
    preferred_crop_labels: List[str] = Field(default_factory=list)
    distance_km: Optional[float] = Field(default=None, description="Distance from the active centre")


class B2BBuyersResponse(BaseModel):
    centre_id: str
    total: int = 0
    buyers: List[B2BBuyerOut] = Field(default_factory=list)


class B2BMatchRequest(BaseModel):
    centre_id: str = "DAMBULLA"
    crops: Optional[List[str]] = Field(default=None, description="Defaults to the standard crop basket")


class B2BMatchOut(BaseModel):
    buyer_code: str
    company_name: str
    crop_name: str
    crop_label: str
    matched_volume_tons: float
    fefo_risk_score: float = Field(..., ge=0.0, le=1.0, description="0.0 = best match, 1.0 = worst")
    recommended_action: str


class B2BMatchResponse(BaseModel):
    centre_id: str
    anomaly_count: int = 0
    total_volume_tons: float = 0.0
    average_fefo_score: float = 0.0
    matches: List[B2BMatchOut] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# B2B Quota Allocation & Agreement Schemas
# --------------------------------------------------------------------------- #
class B2BQuotaCreate(BaseModel):
    centre_id: str = "DAMBULLA"
    buyer_code: str
    buyer_name: str
    buyer_location: Optional[str] = None
    crop_name: str
    crop_grade: str = "Grade A (Processing Quality)"
    total_surplus_tons: float = 25.0
    allocated_quota_tons: float
    offered_price_per_kg: float
    delivery_deadline: str
    shelf_life_days: int = 4
    distance_km: float = 100.0
    fefo_score: float = 0.85
    status: str = "OFFER_SENT"  # DRAFT | OFFER_SENT | ACCEPTED | CONTRACTED | REJECTED
    notes: Optional[str] = None


class B2BQuotaUpdateStatus(BaseModel):
    status: str  # DRAFT | OFFER_SENT | ACCEPTED | CONTRACTED | REJECTED
    notes: Optional[str] = None


class B2BQuotaOut(BaseModel):
    id: int
    user_id: int
    centre_id: str
    buyer_code: str
    buyer_name: str
    buyer_location: Optional[str] = None
    crop_name: str
    crop_grade: str
    total_surplus_tons: float
    allocated_quota_tons: float
    offered_price_per_kg: float
    delivery_deadline: str
    shelf_life_days: int
    distance_km: float
    fefo_score: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class B2BQuotaListResponse(BaseModel):
    total: int
    quotas: List[B2BQuotaOut]


# --------------------------------------------------------------------------- #
# Scraper / Market Price Sync Schemas
# --------------------------------------------------------------------------- #
class SyncPricesRequest(BaseModel):
    """Request body for POST /api/market/sync-prices."""
    centre_id: Optional[str] = Field(
        default=None,
        description="Centre to sync. Omit to sync ALL centres."
    )


class SyncPricesResult(BaseModel):
    """Per-centre result returned by the sync endpoint."""
    centre_id:          str
    date:               str
    crops_synced:       int
    inserted:           int
    updated:            int
    live_prices_found:  int = 0


class SyncPricesResponse(BaseModel):
    """Response body for POST /api/market/sync-prices."""
    results:   List[SyncPricesResult]
    synced_at: datetime = Field(default_factory=_utcnow)


class ManualPriceUpdateRequest(BaseModel):
    """Admin override for a single crop price."""
    centre_id:   str   = Field(..., examples=["DAMBULLA"])
    crop_name:   str   = Field(..., examples=["tomato"])
    price_lkr:   float = Field(..., gt=0, le=10_000, description="Wholesale price LKR/kg")
    supply_tons: float = Field(..., ge=0, le=10_000, description="Supply volume in metric tons")
    date:        Optional[str] = Field(
        default=None,
        description="ISO date string YYYY-MM-DD (defaults to today)"
    )


class ManualPriceUpdateResponse(BaseModel):
    centre_id:   str
    crop:        str
    crop_label:  str
    price_lkr:   float
    supply_tons: float
    date:        str
    action:      str   # "inserted" | "updated"


class SeedBaselineRequest(BaseModel):
    """Request body for POST /api/market/seed-baseline."""
    days: int = Field(default=60, ge=7, le=365, description="Days of historical data to seed")


class SeedBaselineResponse(BaseModel):
    days_seeded:    int
    centres:        List[str]
    crops:          List[str]
    total_inserted: int
    total_updated:  int
    seeded_at:      datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class ErrorResponse(BaseModel):
    detail: str
    error_type: str = "server_error"

