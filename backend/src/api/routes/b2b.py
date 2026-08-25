from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.auth.dependencies import get_current_user
from src.infrastructure.db import get_db_session
from src.infrastructure.models import UserModel, B2BQuotaOfferModel

from src.api.schemas import (
    B2BMatchRequest,
    B2BMatchResponse,
    B2BBuyersResponse,
    B2BQuotaCreate,
    B2BQuotaOut,
    B2BQuotaUpdateStatus,
    B2BQuotaListResponse,
)
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


# --------------------------------------------------------------------------- #
# B2B Quota Allocation & Agreement Routes
# --------------------------------------------------------------------------- #

@router.post("/quotas", response_model=B2BQuotaOut, status_code=status.HTTP_201_CREATED)
async def create_quota_offer(
    payload: B2BQuotaCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> B2BQuotaOut:
    """Creates a new B2B quota offer / supply agreement."""
    logger.info(f"[b2b/quotas] user={current_user.id} buyer={payload.buyer_code} crop={payload.crop_name} tons={payload.allocated_quota_tons}")

    record = B2BQuotaOfferModel(
        user_id=current_user.id,
        centre_id=payload.centre_id,
        buyer_code=payload.buyer_code,
        buyer_name=payload.buyer_name,
        buyer_location=payload.buyer_location,
        crop_name=payload.crop_name,
        crop_grade=payload.crop_grade,
        total_surplus_tons=payload.total_surplus_tons,
        allocated_quota_tons=payload.allocated_quota_tons,
        offered_price_per_kg=payload.offered_price_per_kg,
        delivery_deadline=payload.delivery_deadline,
        shelf_life_days=payload.shelf_life_days,
        distance_km=payload.distance_km,
        fefo_score=payload.fefo_score,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return B2BQuotaOut.model_validate(record)


@router.get("/quotas", response_model=B2BQuotaListResponse)
async def list_quota_offers(
    centre_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> B2BQuotaListResponse:
    """Lists all active and archived B2B quota offers for the authenticated user."""
    stmt = (
        select(B2BQuotaOfferModel)
        .where(B2BQuotaOfferModel.user_id == current_user.id)
        .order_by(desc(B2BQuotaOfferModel.created_at))
    )

    if centre_id:
        stmt = stmt.where(B2BQuotaOfferModel.centre_id == centre_id.upper())
    if status_filter:
        stmt = stmt.where(B2BQuotaOfferModel.status == status_filter.upper())

    result = await db.execute(stmt)
    records = result.scalars().all()

    return B2BQuotaListResponse(
        total=len(records),
        quotas=[B2BQuotaOut.model_validate(r) for r in records],
    )


@router.patch("/quotas/{quota_id}/status", response_model=B2BQuotaOut)
async def update_quota_status(
    quota_id: int,
    payload: B2BQuotaUpdateStatus,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> B2BQuotaOut:
    """Updates the lifecycle state of a quota offer (DRAFT -> OFFER_SENT -> ACCEPTED -> CONTRACTED -> REJECTED)."""
    stmt = select(B2BQuotaOfferModel).where(
        B2BQuotaOfferModel.id == quota_id,
        B2BQuotaOfferModel.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Quota offer not found.")

    record.status = payload.status
    if payload.notes:
        record.notes = payload.notes

    await db.commit()
    await db.refresh(record)
    logger.info(f"[b2b/quotas/{quota_id}] status updated to {record.status}")
    return B2BQuotaOut.model_validate(record)


@router.delete("/quotas/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota_offer(
    quota_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Deletes a quota offer."""
    stmt = select(B2BQuotaOfferModel).where(
        B2BQuotaOfferModel.id == quota_id,
        B2BQuotaOfferModel.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Quota offer not found.")

    await db.delete(record)
    await db.commit()
    logger.info(f"[b2b/quotas/{quota_id}] deleted successfully")
    return None
