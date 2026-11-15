import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import Customer, LoyaltyAccount, Tier
from backend.app.schemas.loyalty import CustomerCreateRequest
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import NotFoundError, ConflictError, BadRequestError
from backend.app.core.logging import logger


class CustomerService:
    """
    Workflow A: Customer and Loyalty Account Provisioning.
    Guarantees unique 1:1 customer-to-account mapping, default Bronze tier,
    zero starting balance, and full audit traceability.
    """

    @classmethod
    async def provision_customer(
        cls,
        db: AsyncSession,
        req: CustomerCreateRequest,
        actor_id: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> Tuple[Customer, LoyaltyAccount, bool]:
        # 1. Check if customer with matching email already exists
        stmt = select(Customer).options(selectinload(Customer.loyalty_account)).where(Customer.email == req.email.lower().strip())
        result = await db.execute(stmt)
        existing_cust = result.scalar_one_or_none()

        if existing_cust:
            # If already provisioned, return existing customer and account idempotently
            logger.info(f"Customer with email {req.email} already exists ({existing_cust.customer_id}). Returning existing profile.")
            return existing_cust, existing_cust.loyalty_account, False

        # 2. Determine Customer ID
        customer_id = req.customer_id
        if not customer_id:
            customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        else:
            # Check ID uniqueness
            chk_stmt = select(Customer).where(Customer.customer_id == customer_id)
            chk_res = await db.execute(chk_stmt)
            if chk_res.scalar_one_or_none():
                raise ConflictError(detail=f"Customer ID '{customer_id}' is already registered.")

        # 3. Create Customer
        new_customer = Customer(
            customer_id=customer_id,
            user_id=user_id,
            email=req.email.lower().strip(),
            first_name=req.first_name.strip(),
            last_name=req.last_name.strip(),
            phone=req.phone.strip() if req.phone else None,
            status="ACTIVE",
        )
        db.add(new_customer)
        await db.flush()

        # 4. Ensure Default Bronze Tier exists
        tier_stmt = select(Tier).where(Tier.tier_id == "TIER-BRONZE")
        tier_res = await db.execute(tier_stmt)
        bronze_tier = tier_res.scalar_one_or_none()
        if not bronze_tier:
            bronze_tier = Tier(
                tier_id="TIER-BRONZE",
                name="Bronze",
                rank=1,
                min_spend=Decimal("0.00"),
                earning_multiplier=Decimal("1.00"),
            )
            db.add(bronze_tier)
            await db.flush()

        # 5. Create 1:1 Loyalty Account
        account_id = f"LOY-{customer_id}"
        new_account = LoyaltyAccount(
            account_id=account_id,
            customer_id=customer_id,
            tier_id="TIER-BRONZE",
            current_balance=0,
            lifetime_accrued=0,
            lifetime_redeemed=0,
            qualifying_spend=Decimal("0.00"),
            status="ACTIVE",
        )
        db.add(new_account)
        await db.flush()

        # 6. Audit Trail
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="CUSTOMER_PROVISIONED",
            entity_type="loyalty_accounts",
            entity_id=account_id,
            metadata={
                "customer_id": customer_id,
                "email": new_customer.email,
                "initial_tier": "TIER-BRONZE",
                "initial_balance": 0,
            },
        )

        await db.commit()
        await db.refresh(new_customer)
        await db.refresh(new_account)

        return new_customer, new_account, True

    @classmethod
    async def get_customer(cls, db: AsyncSession, customer_id: str) -> Customer:
        stmt = select(Customer).options(selectinload(Customer.loyalty_account)).where(Customer.customer_id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        if not customer:
            raise NotFoundError(detail=f"Customer '{customer_id}' not found.")
        return customer

    @classmethod
    async def get_account_by_customer_id(cls, db: AsyncSession, customer_id: str) -> LoyaltyAccount:
        stmt = select(LoyaltyAccount).options(selectinload(LoyaltyAccount.tier)).where(LoyaltyAccount.customer_id == customer_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise NotFoundError(detail=f"Loyalty account for customer '{customer_id}' not found.")
        return account

    @classmethod
    async def get_account(cls, db: AsyncSession, account_id: str) -> LoyaltyAccount:
        stmt = select(LoyaltyAccount).options(selectinload(LoyaltyAccount.tier)).where(LoyaltyAccount.account_id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise NotFoundError(detail=f"Loyalty account '{account_id}' not found.")
        return account
