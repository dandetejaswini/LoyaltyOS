from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, func
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import Tier, LoyaltyAccount, Order, OrderReturn
from backend.app.schemas.loyalty import TierResponse, TierCalculationResponse
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import NotFoundError
from backend.app.core.logging import logger


class TierService:
    """
    Workflow G: Tier Management & Rolling 365-Day Qualifying Spend Evaluation.
    Enforces qualifying net spend evaluation (excluding tax/shipping/gift cards)
    and executes tier upgrades with full audit tracking.
    """

    @classmethod
    async def list_tiers(cls, db: AsyncSession) -> List[TierResponse]:
        query = select(Tier).order_by(asc(Tier.rank))
        tiers = (await db.execute(query)).scalars().all()
        return [
            TierResponse(
                tier_id=t.tier_id,
                name=t.name,
                rank=t.rank,
                min_spend=t.min_spend,
                earning_multiplier=t.earning_multiplier,
            )
            for t in tiers
        ]

    @classmethod
    async def evaluate_account_tier(
        cls,
        db: AsyncSession,
        account_id: str,
        actor_id: str,
    ) -> TierCalculationResponse:
        acc_stmt = select(LoyaltyAccount).options(selectinload(LoyaltyAccount.tier)).where(LoyaltyAccount.account_id == account_id).with_for_update()
        account = (await db.execute(acc_stmt)).scalar_one_or_none()
        if not account:
            raise NotFoundError(detail=f"Loyalty account '{account_id}' not found.")

        # 1. Compute rolling 365-day qualifying spend
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=365)

        # Sum eligible net spend from completed orders within the window
        order_spend_stmt = (
            select(func.coalesce(func.sum(Order.eligible_net_spend), Decimal("0.00")))
            .where(
                Order.customer_id == account.customer_id,
                Order.status.in_(["COMPLETED", "RETURNED"]),
                Order.order_date >= window_start,
            )
        )
        total_order_spend = (await db.execute(order_spend_stmt)).scalar() or Decimal("0.00")

        # Sum refund amounts from returns within the window
        refund_stmt = (
            select(func.coalesce(func.sum(OrderReturn.total_refund_amount), Decimal("0.00")))
            .join(Order, Order.order_id == OrderReturn.order_id)
            .where(
                Order.customer_id == account.customer_id,
                OrderReturn.status == "PROCESSED",
                OrderReturn.created_at >= window_start,
            )
        )
        total_refunds = (await db.execute(refund_stmt)).scalar() or Decimal("0.00")

        qualifying_spend_365d = max(Decimal("0.00"), total_order_spend - total_refunds)

        # 2. Determine target tier based on qualifying spend
        tiers = (await db.execute(select(Tier).order_by(asc(Tier.min_spend)))).scalars().all()
        target_tier = tiers[0] if tiers else account.tier
        for t in tiers:
            if qualifying_spend_365d >= t.min_spend:
                target_tier = t

        previous_tier_id = account.tier_id
        is_upgrade = target_tier.rank > (account.tier.rank if account.tier else 1)
        is_downgrade = target_tier.rank < (account.tier.rank if account.tier else 1)

        # 3. Apply Tier change if appropriate
        if target_tier.tier_id != account.tier_id:
            account.tier_id = target_tier.tier_id
            account.updated_at = now

            # Audit event
            action = "TIER_UPGRADE" if is_upgrade else "TIER_DOWNGRADE"
            await AuditService.log_event(
                db=db,
                actor_id=actor_id,
                action=action,
                entity_type="loyalty_accounts",
                entity_id=account.account_id,
                metadata={
                    "previous_tier": previous_tier_id,
                    "new_tier": target_tier.tier_id,
                    "qualifying_spend_365d": str(qualifying_spend_365d),
                }
            )
            await db.commit()

        return TierCalculationResponse(
            account_id=account.account_id,
            customer_id=account.customer_id,
            current_tier_id=target_tier.tier_id,
            previous_tier_id=previous_tier_id if (is_upgrade or is_downgrade) else None,
            qualifying_spend_365d=qualifying_spend_365d,
            multiplier=target_tier.earning_multiplier,
            is_upgrade=is_upgrade,
            is_downgrade=is_downgrade,
            evaluation_time=now,
        )
