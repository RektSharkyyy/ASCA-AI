"""
B2B matching API routes.

GET  /api/b2b/buyers   ?centre_id=DAMBULLA
POST /api/b2b/match
"""

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user
from src.infrastructure.models import UserModel

from src.api.schemas import B2BMatchRequest, B2BMatchResponse, B2BBuyersResponse
from src.infrastructure.logging import logger
from src.services.b2b_service import b2b_service

router = APIRouter(prefix="/api/b2b", tags=["b2b"])


@router.get("/buyers", response_model=B2BBuyersResponse)
async def list_buyers(
    centre_id: str = Query(default="DAMBULLA", description="Economic centre ID"),
    _user: UserModel = Depends(get_current_user),
) -> B2BBuyersResponse:
    """
    Returns the full ChromaDB buyer registry annotated with distances from the
    active economic centre. Used by the B2B Directory view.
    """
    logger.info(f"[b2b/buyers] centre={centre_id}")
    return await b2b_service.list_buyers(centre_id)


@router.post("/match", response_model=B2BMatchResponse)
async def match_surplus(
    req: B2BMatchRequest,
    _user: UserModel = Depends(get_current_user),
) -> B2BMatchResponse:
    """
    Scouts the crop basket for surplus anomalies then FEFO-ranks available buyers.
    Returns an empty `matches` list (not an error) when the market is healthy.
    """
    logger.info(f"[b2b/match] centre={req.centre_id} crops={req.crops}")
    return await b2b_service.match_surplus(req.centre_id, req.crops)
