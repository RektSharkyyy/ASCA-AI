"""
Cultivation Advisory API Routes
────────────────────────────────
GET  /api/cultivation/crops                 — List all crops with agronomic profiles
POST /api/cultivation/recommend             — AI-ranked crop recommendations for given farm params
GET  /api/cultivation/guide/{crop_id}       — Full step-by-step guide, fertilizer schedule & pest management
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user
from src.infrastructure.models import UserModel
from src.infrastructure.logging import logger
from src.services.cultivation_service import (
    get_all_crops,
    get_crop_guide,
    get_recommendations,
)

router = APIRouter(prefix="/api/cultivation", tags=["cultivation"])


# ─── Request / Response schemas ─────────────────────────────────────────────

class RecommendRequest(BaseModel):
    centre_id: str = Field(default="DAMBULLA", description="Economic centre ID")
    season: str = Field(default="Maha", description="Maha or Yala")
    soil_type: str = Field(default="Reddish Brown Earth", description="Dominant soil type")
    water_source: str = Field(default="Agrowell", description="Primary water source")
    land_area_acres: float = Field(default=1.0, ge=0.1, le=100.0, description="Total cultivable area in acres")


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/crops")
async def list_crops(
    _user: UserModel = Depends(get_current_user),
):
    """
    Returns summary cards for all crops in the DOA agronomic knowledge base.
    Used to populate the crop picker UI in the Cultivation Planner view.
    """
    logger.info("[cultivation/crops] listing all crop profiles")
    return {"crops": get_all_crops()}


@router.post("/recommend")
async def recommend_crops(
    req: RecommendRequest,
    _user: UserModel = Depends(get_current_user),
):
    """
    Ranks and recommends crops for the given farm parameters using a
    multi-factor scoring model (ROI × Market Demand × Seasonal Fit × Soil Fit).
    Returns estimated yield, gross revenue, net profit and ROI for the user's land size.
    """
    logger.info(
        f"[cultivation/recommend] centre={req.centre_id} season={req.season} "
        f"soil={req.soil_type} water={req.water_source} acres={req.land_area_acres}"
    )
    ranked = get_recommendations(
        season=req.season,
        soil_type=req.soil_type,
        water_source=req.water_source,
        land_area_acres=req.land_area_acres,
        centre_id=req.centre_id,
    )
    return {
        "centre_id": req.centre_id,
        "season": req.season,
        "soil_type": req.soil_type,
        "water_source": req.water_source,
        "land_area_acres": req.land_area_acres,
        "recommendations": ranked,
    }


@router.get("/guide/{crop_id}")
async def get_cultivation_guide(
    crop_id: str,
    _user: UserModel = Depends(get_current_user),
):
    """
    Returns the complete cultivation guide for a specific crop including:
    - 6-stage step-by-step lifecycle timeline (24 weeks)
    - DOA-approved fertilizer and nutrition schedule
    - Pest and disease identification with organic + IPM controls
    """
    logger.info(f"[cultivation/guide] crop_id={crop_id}")
    guide = get_crop_guide(crop_id.lower().replace(" ", "_").replace("-", "_"))
    if not guide:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No cultivation guide found for crop: {crop_id}")
    return guide
