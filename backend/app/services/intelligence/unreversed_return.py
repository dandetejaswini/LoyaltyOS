import math
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import Order, OrderReturn, LoyaltyAccount
from backend.app.models.ledger import PointsTransaction
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding


class UnreversedReturnDetector(BaseDetector):
    """
    Detector 3: Unreversed Return & Cumulative Reversal Cap (BR-09 / BR-10).
    Identifies order returns where refund amounts were processed but corresponding
    loyalty points were either not reversed or insufficiently reversed on the ledger.
    Respects the original accrual cap and partial refund proportionality.
    """

    def __init__(self):
        super().__init__(
            detector_id="DET-UNREVERSED-RETURN",
            category="UNREVERSED_RETURN",
            name="Unreversed Return & Refund Reversal Integrity Detector",
        )

    async def detect(
        self,
        db: AsyncSession,
        account_id: Optional[str] = None,
        **kwargs
    ) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        # 1. Query processed order returns
        query = select(OrderReturn).options(
            selectinload(OrderReturn.order).selectinload(Order.customer)
        ).where(OrderReturn.status == "PROCESSED")

        returns = (await db.execute(query)).scalars().all()

        for ret in returns:
            order = ret.order
            if not order:
                continue

            # If scoped to an account_id, check if customer matches account
            if account_id:
                acc_check = await db.execute(
                    select(LoyaltyAccount.customer_id).where(LoyaltyAccount.account_id == account_id)
                )
                target_cust_id = acc_check.scalar_one_or_none()
                if target_cust_id != order.customer_id:
                    continue

            # 2. Find original accrual transaction for the order
            accrual_stmt = select(PointsTransaction).where(
                PointsTransaction.order_id == order.order_id,
                PointsTransaction.entry_type == "ACCRUAL",
            )
            accrual_tx = (await db.execute(accrual_stmt)).scalar_one_or_none()

            original_accrual_pts = accrual_tx.points if accrual_tx else 0
            original_accrual_tx_id = accrual_tx.transaction_id if accrual_tx else None

            # If no points were ever accrued for this order, no reversal is expected
            if original_accrual_pts <= 0:
                continue

            # 3. Calculate expected reversal points
            refund_amount = Decimal(str(ret.total_refund_amount))
            if refund_amount <= Decimal("0.00"):
                continue

            # Proportional calculation based on order net spend vs refund amount
            eligible_spend = Decimal(str(order.eligible_net_spend))
            if eligible_spend > Decimal("0.00"):
                spend_ratio = min(Decimal("1.0"), refund_amount / eligible_spend)
                expected_reversal = min(
                    original_accrual_pts,
                    math.floor(float(Decimal(original_accrual_pts) * spend_ratio))
                )
            else:
                expected_reversal = min(original_accrual_pts, math.floor(float(refund_amount)))

            # If full return type, expected is capped at total original accrual
            if ret.return_type == "FULL":
                expected_reversal = original_accrual_pts

            # 4. Query actual reversal points on ledger for this order
            rev_tx_stmt = select(func.coalesce(func.sum(func.abs(PointsTransaction.points)), 0)).where(
                PointsTransaction.order_id == order.order_id,
                PointsTransaction.entry_type == "REVERSAL",
            )
            ledger_reversed_pts = (await db.execute(rev_tx_stmt)).scalar() or 0

            # Combined actual reversal recorded
            actual_reversal = max(ret.points_reversed, ledger_reversed_pts)

            # Check if discrepancy exists
            if actual_reversal < expected_reversal:
                missing_points = expected_reversal - actual_reversal

                if missing_points >= 100 or ret.points_reversed == 0:
                    severity = "HIGH"
                    severity_reason = (
                        f"HIGH financial leakage: Return {ret.return_id} refunded ${refund_amount} on order "
                        f"{order.order_id}, but {missing_points} points were not reversed. "
                        f"Customer retains unearned rewards post-refund, violating BR-09 / BR-10."
                    )
                else:
                    severity = "MEDIUM"
                    severity_reason = (
                        f"MEDIUM reversal discrepancy: Return {ret.return_id} has {missing_points} points "
                        f"unreversed following refund."
                    )

                what_happened = (
                    f"Unreversed return detected: Return {ret.return_id} on order {order.order_id} refunded "
                    f"${refund_amount}, expecting {expected_reversal} points to be reversed based on original accrual "
                    f"of {original_accrual_pts} points, but only {actual_reversal} points were reversed (missing: {missing_points} pts)."
                )

                description = (
                    f"Return {ret.return_id} (Order {order.order_id}): Refund ${refund_amount}. "
                    f"Expected reversal: {expected_reversal} pts. Actual reversal: {actual_reversal} pts. "
                    f"Missing reversal: {missing_points} pts."
                )

                recommendation = (
                    f"1. Audit e-commerce return integration webhooks for order {order.order_id} to identify dropped reversal events. "
                    f"2. Verify whether returned merchandise was restocked. "
                    f"3. Issue an operator-approved REVERSAL transaction for {missing_points} points linked to order {order.order_id}."
                )

                finding = AnomalyFinding(
                    detector_id=self.detector_id,
                    category=self.category,
                    entity_type="ORDER_RETURN",
                    entity_id=ret.return_id,
                    variance_amount=Decimal(str(missing_points)),
                    severity=severity,
                    severity_reason=severity_reason,
                    rule_violated="BR-09 / BR-10: Points Reversal on Return (Returned merchandise points must be proportionally reversed)",
                    what_happened=what_happened,
                    description=description,
                    evidence={
                        "return_id": ret.return_id,
                        "order_id": order.order_id,
                        "customer_id": order.customer_id,
                        "return_type": ret.return_type,
                        "total_refund_amount": str(refund_amount),
                        "eligible_net_spend": str(order.eligible_net_spend),
                        "original_accrual_transaction_id": original_accrual_tx_id,
                        "original_points_accrued": original_accrual_pts,
                        "expected_reversal_points": expected_reversal,
                        "actual_reversal_points": actual_reversal,
                        "missing_points": missing_points,
                        "return_created_at": ret.created_at.isoformat() if ret.created_at else None,
                    },
                    discrepancy_calculation={
                        "formula": "expected_reversal_points - actual_reversal_points",
                        "expected_reversal_points": expected_reversal,
                        "actual_reversal_points": actual_reversal,
                        "missing_points": missing_points,
                        "accrual_cap": original_accrual_pts,
                    },
                    recommendation=recommendation,
                )
                findings.append(finding)

        return findings
