from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer
from backend.app.schemas.ledger import RewardResponse, RedemptionRequest, RedemptionResponse
from backend.app.services.redemption_service import RedemptionService
from backend.app.services.customer_service import CustomerService
from backend.app.core.errors import ForbiddenError

router = APIRouter(prefix="/redemptions", tags=["Rewards & Points Redemptions"])


@router.get("/rewards", response_model=List[RewardResponse])
async def list_available_rewards(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Lists active reward vouchers from the rewards catalog.
    """
    return await RedemptionService.list_available_rewards(db=db, active_only=True)


@router.post("/redeem", response_model=RedemptionResponse, status_code=status.HTTP_201_CREATED)
async def redeem_reward_voucher(
    req: RedemptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow D: Concurrency-Safe Reward Redemption.
    Allocates points using FIFO lot consumption, checks positive balance,
    locks account row against race conditions, and generates a voucher code.
    """
    if current_user.role == "CUSTOMER":
        account = await CustomerService.get_account(db, req.account_id)
        stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != account.customer_id:
            raise ForbiddenError(detail="Customers can only redeem points from their own account.")

    return await RedemptionService.redeem_reward(
        db=db,
        req=req,
        actor_id=str(current_user.id),
    )
