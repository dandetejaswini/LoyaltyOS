from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer
from backend.app.schemas.loyalty import TierResponse, TierCalculationResponse
from backend.app.services.tier_service import TierService
from backend.app.services.customer_service import CustomerService
from backend.app.core.errors import ForbiddenError

router = APIRouter(prefix="/tiers", tags=["Tier Management & Multipliers"])


@router.get("", response_model=List[TierResponse])
async def list_tiers(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Lists all loyalty tier configurations, spend thresholds, and earning multipliers.
    """
    return await TierService.list_tiers(db=db)


@router.post("/accounts/{account_id}/evaluate", response_model=TierCalculationResponse)
async def evaluate_account_tier(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow G: Evaluates 365-day rolling qualifying spend and executes tier upgrades.
    """
    if current_user.role == "CUSTOMER":
        account = await CustomerService.get_account(db, account_id)
        stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != account.customer_id:
            raise ForbiddenError(detail="Customers can only evaluate their own account tier.")

    return await TierService.evaluate_account_tier(
        db=db,
        account_id=account_id,
        actor_id=str(current_user.id),
    )
