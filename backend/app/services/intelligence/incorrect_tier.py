from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, func
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import LoyaltyAccount, Tier, Order, OrderReturn
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding


class IncorrectTierDetector(BaseDetector):
    """
    Detector 5: Incorrect Tier Calculation & Gross Spend Inflation (BR-06 / BR-07).
    Identifies loyalty accounts where the current assigned tier exceeds the tier
    justified by the customer's rolling 365-day qualifying net spend.
    Detects improper inclusion of sales tax, shipping fees, or ineligible items
    in tier evaluations.
    """

    def __init__(self):
        super().__init__(
            detector_id="DET-INCORRECT-TIER",
            category="INCORRECT_TIER",
            name="Tier Qualification & Gross Spend Inflation Detector",
        )

    async def detect(
        self,
        db: AsyncSession,
        account_id: Optional[str] = None,
        **kwargs
    ) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        # 1. Fetch tier definitions sorted by rank ascending
        tiers = (await db.execute(select(Tier).order_by(asc(Tier.rank)))).scalars().all()
        if not tiers:
            return findings

        # 2. Query loyalty accounts
        acc_query = select(LoyaltyAccount).options(selectinload(LoyaltyAccount.tier))
        if account_id:
            acc_query = acc_query.where(LoyaltyAccount.account_id == account_id)
        accounts = (await db.execute(acc_query)).scalars().all()

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=365)

        for acc in accounts:
            current_tier = acc.tier
            if not current_tier:
                continue

            # 3. Reconstruct rolling 365-day qualifying net spend from source orders
            order_spend_stmt = (
                select(
                    func.coalesce(func.sum(Order.eligible_net_spend), Decimal("0.00")),
                    func.coalesce(func.sum(Order.gross_amount), Decimal("0.00")),
                    func.count(Order.order_id),
                )
                .where(
                    Order.customer_id == acc.customer_id,
                    Order.status.in_(["COMPLETED", "RETURNED"]),
                    Order.order_date >= window_start,
                )
            )
            spend_row = (await db.execute(order_spend_stmt)).first()
            total_net_spend = spend_row[0] if spend_row else Decimal("0.00")
            total_gross_spend = spend_row[1] if spend_row else Decimal("0.00")
            order_count = spend_row[2] if spend_row else 0

            # 4. Subtract refunds in rolling window
            refund_stmt = (
                select(func.coalesce(func.sum(OrderReturn.total_refund_amount), Decimal("0.00")))
                .join(Order, Order.order_id == OrderReturn.order_id)
                .where(
                    Order.customer_id == acc.customer_id,
                    OrderReturn.status == "PROCESSED",
                    OrderReturn.created_at >= window_start,
                )
            )
            total_refunds = (await db.execute(refund_stmt)).scalar() or Decimal("0.00")

            reconstructed_qualifying_spend = max(Decimal("0.00"), total_net_spend - total_refunds)

            # Also check account.qualifying_spend column if stored
            stored_qualifying_spend = Decimal(str(acc.qualifying_spend))

            # 5. Determine expected tier based on reconstructed qualifying spend
            expected_tier = tiers[0]
            for t in tiers:
                if reconstructed_qualifying_spend >= Decimal(str(t.min_spend)):
                    expected_tier = t

            # 6. Check if current tier rank exceeds expected tier rank
            if current_tier.rank > expected_tier.rank:
                min_spend_required = Decimal(str(current_tier.min_spend))
                spend_deficit = max(Decimal("0.00"), min_spend_required - reconstructed_qualifying_spend)

                # Check if gross spend was the source of inflation
                is_gross_inflation = (total_gross_spend >= min_spend_required > reconstructed_qualifying_spend)

                if spend_deficit >= Decimal("2000.00"):
                    severity = "HIGH"
                    severity_reason = (
                        f"HIGH tier privilege inflation: Customer {acc.customer_id} is assigned {current_tier.name} "
                        f"(requires ${min_spend_required:.2f}) with only ${reconstructed_qualifying_spend:.2f} in "
                        f"reconstructed qualifying spend (deficit: ${spend_deficit:.2f})."
                    )
                else:
                    severity = "MEDIUM"
                    severity_reason = (
                        f"MEDIUM tier policy inconsistency: Account {acc.account_id} tier '{current_tier.name}' "
                        f"exceeds justified tier '{expected_tier.name}' based on rolling 365-day qualifying net spend."
                    )

                what_happened = (
                    f"Incorrect tier assignment detected on account {acc.account_id} (Customer {acc.customer_id}): "
                    f"currently assigned to {current_tier.name} (min spend: ${min_spend_required:.2f}), but "
                    f"reconstructed qualifying net spend is only ${reconstructed_qualifying_spend:.2f}. "
                    f"Expected tier: {expected_tier.name}."
                )

                description = (
                    f"Account {acc.account_id}: Current tier '{current_tier.name}' (Rank {current_tier.rank}) vs "
                    f"Expected tier '{expected_tier.name}' (Rank {expected_tier.rank}). "
                    f"Qualifying Net Spend: ${reconstructed_qualifying_spend:.2f}, Gross Spend: ${total_gross_spend:.2f}, "
                    f"Spend Deficit: ${spend_deficit:.2f}."
                )

                recommendation = (
                    f"1. Audit order line items for account {acc.account_id} to verify if sales tax or shipping "
                    f"amounts were inadvertently included in tier calculation. "
                    f"2. Check if a manual tier override was performed by customer support without documentation. "
                    f"3. Re-evaluate customer tier using POST /api/v1/tiers/accounts/{acc.account_id}/evaluate."
                )

                finding = AnomalyFinding(
                    detector_id=self.detector_id,
                    category=self.category,
                    entity_type="ACCOUNT",
                    entity_id=acc.account_id,
                    variance_amount=spend_deficit,
                    severity=severity,
                    severity_reason=severity_reason,
                    rule_violated="BR-06 / BR-07: Qualifying Spend vs Gross Spend (Tiers must be calculated on net merchandise spend only)",
                    what_happened=what_happened,
                    description=description,
                    evidence={
                        "account_id": acc.account_id,
                        "customer_id": acc.customer_id,
                        "current_tier_id": current_tier.tier_id,
                        "current_tier_name": current_tier.name,
                        "current_tier_rank": current_tier.rank,
                        "expected_tier_id": expected_tier.tier_id,
                        "expected_tier_name": expected_tier.name,
                        "expected_tier_rank": expected_tier.rank,
                        "reconstructed_qualifying_spend": str(reconstructed_qualifying_spend),
                        "reconstructed_gross_spend": str(total_gross_spend),
                        "stored_qualifying_spend": str(stored_qualifying_spend),
                        "tier_min_spend_required": str(min_spend_required),
                        "spend_deficit": str(spend_deficit),
                        "orders_in_window_count": order_count,
                        "is_gross_inflation_suspected": is_gross_inflation,
                    },
                    discrepancy_calculation={
                        "formula": "tier_min_spend_required - reconstructed_qualifying_spend",
                        "tier_min_spend_required": str(min_spend_required),
                        "reconstructed_qualifying_spend": str(reconstructed_qualifying_spend),
                        "spend_deficit": str(spend_deficit),
                    },
                    recommendation=recommendation,
                )
                findings.append(finding)

        return findings
