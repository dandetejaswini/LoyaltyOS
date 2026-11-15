from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_operator
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Order
from backend.app.schemas.loyalty import OrderCreateRequest, OrderAccrualResponse, OrderLineResponse
from backend.app.services.accrual_service import AccrualService
from backend.app.core.errors import NotFoundError, ForbiddenError

router = APIRouter(prefix="/orders", tags=["Orders & Points Accrual"])


@router.post("/accrue", response_model=OrderAccrualResponse, status_code=status.HTTP_201_CREATED)
async def create_order_and_accrue_points(
    req: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow B: Atomic Order Creation and Points Accrual.
    Validates merchandise eligibility, applies tier multipliers, floors fractional points,
    and updates the append-only points journal and FIFO lot.
    """
    # Customer ownership check: Customers can only submit orders for themselves
    if current_user.role == "CUSTOMER":
        from backend.app.models.loyalty import Customer
        stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != req.customer_id:
            raise ForbiddenError(detail="Customers can only accrue points for their own customer ID.")

    return await AccrualService.process_order_accrual(
        db=db,
        req=req,
        actor_id=str(current_user.id),
    )


@router.get("/{order_id}")
async def get_order_by_id(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Retrieves order details and order lines.
    """
    stmt = select(Order).options(selectinload(Order.lines)).where(Order.order_id == order_id)
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise NotFoundError(detail=f"Order '{order_id}' not found.")

    if current_user.role == "CUSTOMER":
        from backend.app.models.loyalty import Customer
        cust_stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(cust_stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != order.customer_id:
            raise ForbiddenError(detail="Access denied: You may only view your own orders.")

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "gross_amount": order.gross_amount,
        "tax_amount": order.tax_amount,
        "shipping_amount": order.shipping_amount,
        "discount_amount": order.discount_amount,
        "eligible_net_spend": order.eligible_net_spend,
        "status": order.status,
        "accrual_status": order.accrual_status,
        "lines": [
            OrderLineResponse.model_validate(l) for l in order.lines
        ]
    }
