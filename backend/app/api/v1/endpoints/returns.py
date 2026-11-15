from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_operator
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Order, Customer
from backend.app.schemas.loyalty import OrderReturnRequest, OrderReturnResponse
from backend.app.services.return_service import ReturnService
from backend.app.core.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/returns", tags=["Returns & Points Reversals"])


@router.post("/process", response_model=OrderReturnResponse, status_code=status.HTTP_201_CREATED)
async def process_order_return(
    req: OrderReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow E: Order Return Processing & Points Reversal.
    Reverses points for returned eligible items, caps cumulative reversals at original accrual,
    and supports negative balances when returned items were previously redeemed (BR-10).
    """
    if current_user.role == "CUSTOMER":
        order_stmt = select(Order).where(Order.order_id == req.order_id)
        order = (await db.execute(order_stmt)).scalar_one_or_none()
        if not order:
            raise NotFoundError(detail=f"Order '{req.order_id}' not found.")

        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(cust_stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != order.customer_id:
            raise ForbiddenError(detail="Customers can only initiate returns on their own orders.")

    return await ReturnService.process_return(
        db=db,
        req=req,
        actor_id=str(current_user.id),
    )
