from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_customer, require_operator
from backend.app.models.identity import AppUser
from backend.app.schemas.loyalty import (
    CustomerCreateRequest,
    CustomerProvisionResponse,
    CustomerResponse,
    LoyaltyAccountResponse,
)
from backend.app.services.customer_service import CustomerService
from backend.app.core.errors import ForbiddenError

router = APIRouter(prefix="/accounts", tags=["Customer & Loyalty Accounts"])


@router.post("/provision", response_model=CustomerProvisionResponse, status_code=status.HTTP_201_CREATED)
async def provision_customer_and_account(
    req: CustomerCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow A: Provision a Customer profile and 1:1 Loyalty Account.
    Initializes default Bronze tier, zero starting balance, and full audit trail.
    """
    customer, account, is_new = await CustomerService.provision_customer(
        db=db,
        req=req,
        actor_id=str(current_user.id),
        user_id=current_user.id,
    )
    return CustomerProvisionResponse(
        customer=CustomerResponse.model_validate(customer),
        account=LoyaltyAccountResponse.model_validate(account),
        is_new=is_new,
    )


@router.get("/me", response_model=LoyaltyAccountResponse)
async def get_my_loyalty_account(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(require_customer),
):
    """
    Retrieves the authenticated customer's own loyalty account balance and tier.
    """
    # Find customer associated with this user
    from sqlalchemy import select
    from backend.app.models.loyalty import Customer
    stmt = select(Customer).where(Customer.user_id == current_user.id)
    cust = (await db.execute(stmt)).scalar_one_or_none()
    if not cust:
        # Auto-provision customer profile for authenticated user if not present
        req = CustomerCreateRequest(
            email=current_user.email,
            first_name=current_user.email.split("@")[0].capitalize(),
            last_name="Member",
        )
        _, account, _ = await CustomerService.provision_customer(
            db=db,
            req=req,
            actor_id=str(current_user.id),
            user_id=current_user.id,
        )
        return LoyaltyAccountResponse.model_validate(account)

    account = await CustomerService.get_account_by_customer_id(db, cust.customer_id)
    return LoyaltyAccountResponse.model_validate(account)


@router.get("/{account_id}", response_model=LoyaltyAccountResponse)
async def get_loyalty_account_by_id(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Retrieves account by ID. Customers are restricted to their own account.
    Operators and Operations Managers can inspect any account.
    """
    account = await CustomerService.get_account(db, account_id)
    
    # Ownership verification for customers
    if current_user.role == "CUSTOMER":
        from sqlalchemy import select
        from backend.app.models.loyalty import Customer
        stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != account.customer_id:
            raise ForbiddenError(detail="Access denied: You may only access your own loyalty account.")

    return LoyaltyAccountResponse.model_validate(account)
