"""
Market analytics API routes.

GET  /api/market/forecast       ?centre_id=DAMBULLA&crop=tomato
GET  /api/market/insights       ?centre_id=DAMBULLA
POST /api/market/sync-prices    Trigger HARTI/CBSL scraper → Supabase upsert
POST /api/market/manual-update  Admin override for a specific crop price
POST /api/market/seed-baseline  Seed N days of historical baseline data
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth.dependencies import get_current_user, require_admin
from src.infrastructure.models import UserModel

from src.api.schemas import (
    ManualPriceUpdateRequest,
    ManualPriceUpdateResponse,
    MarketForecastResponse,
    MarketInsightsResponse,
    SeedBaselineRequest,
    SeedBaselineResponse,
    SyncPricesRequest,
    SyncPricesResponse,
    SyncPricesResult,
)
from src.infrastructure.logging import logger
from src.services.market_service import market_service
from src.services.scraper_service import market_scraper, SUPPORTED_CENTRES

router = APIRouter(prefix="/api/market", tags=["market"])


# --------------------------------------------------------------------------- #
# Existing analytics endpoints (read-only)
# --------------------------------------------------------------------------- #

@router.get("/forecast", response_model=MarketForecastResponse)
async def get_forecast(
    centre_id: str = Query(default="DAMBULLA", description="Economic centre ID"),
    crop: str = Query(default="tomato", description="Crop name (snake_case or alias)"),
    _user: UserModel = Depends(get_current_user),
) -> MarketForecastResponse:
    """
    Returns a full 14-day Prophet price-forecast curve for one crop at one centre.
    The `series` list is ready to drop into the Recharts AreaChart on the frontend.
    """
    logger.info(f"[market/forecast] centre={centre_id} crop={crop}")
    return await market_service.get_forecast(centre_id, crop)


@router.get("/insights", response_model=MarketInsightsResponse)
async def get_insights(
    centre_id: str = Query(default="DAMBULLA", description="Economic centre ID"),
    crops: Optional[List[str]] = Query(default=None, description="Crop basket (defaults to standard 6)"),
    _user: UserModel = Depends(get_current_user),
) -> MarketInsightsResponse:
    """
    Parallel-scans the crop basket and returns a summary grid of current vs
    predicted prices, supply volumes, and anomaly flags.
    Powers the Analytics view summary cards.
    """
    logger.info(f"[market/insights] centre={centre_id} crops={crops}")
    return await market_service.get_insights(centre_id, crops)


# --------------------------------------------------------------------------- #
# Scraper / Sync endpoints
# --------------------------------------------------------------------------- #

@router.post("/sync-prices", response_model=SyncPricesResponse)
async def sync_prices(
    req: SyncPricesRequest,
    _user: UserModel = Depends(get_current_user),
) -> SyncPricesResponse:
    """
    Triggers the HARTI / CBSL scraper to fetch today's wholesale prices and
    upsert them into the Supabase `market_data` table.

    - If `centre_id` is specified, only that centre is synced.
    - If omitted, **all supported centres** are synced concurrently.

    Returns per-centre sync stats (inserted / updated counts).
    """
    logger.info(f"[market/sync-prices] triggered by {_user.email}, centre={req.centre_id or 'ALL'}")

    if req.centre_id:
        if req.centre_id.upper() not in SUPPORTED_CENTRES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported centre '{req.centre_id}'. Valid options: {SUPPORTED_CENTRES}",
            )
        raw = [await market_scraper.sync_center_prices(req.centre_id.upper())]
    else:
        raw = await market_scraper.sync_all_centers()

    results = [SyncPricesResult(**r) for r in raw]
    return SyncPricesResponse(results=results)


@router.post("/manual-update", response_model=ManualPriceUpdateResponse)
async def manual_update_price(
    req: ManualPriceUpdateRequest,
    _admin: UserModel = Depends(require_admin),
) -> ManualPriceUpdateResponse:
    """
    Admin-only endpoint: manually set or override the wholesale price and supply
    volume for a specific crop / centre / date in Supabase.

    Useful for:
    - Correcting a scraping error
    - Entering prices for a specific market day
    """
    logger.info(
        f"[market/manual-update] admin={_admin.email} "
        f"centre={req.centre_id} crop={req.crop_name} price={req.price_lkr}"
    )
    target_date = None
    if req.date:
        try:
            target_date = date.fromisoformat(req.date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format '{req.date}'. Use YYYY-MM-DD.",
            )
    try:
        result = await market_scraper.manual_update_price(
            req.centre_id, req.crop_name, req.price_lkr, req.supply_tons, target_date
        )
        return ManualPriceUpdateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/seed-baseline", response_model=SeedBaselineResponse)
async def seed_baseline(
    req: SeedBaselineRequest,
    _admin: UserModel = Depends(require_admin),
) -> SeedBaselineResponse:
    """
    Admin-only: seed the last N days of historical baseline prices into Supabase
    so Prophet never needs the synthetic generator.

    Safe to call multiple times — all upserts are idempotent.
    Defaults to 60 days (the minimum for reliable Prophet seasonality fitting).
    """
    logger.info(f"[market/seed-baseline] admin={_admin.email} days={req.days}")
    result = await market_scraper.seed_historical_baseline(req.days)
    return SeedBaselineResponse(**result)
