from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.app.models.ledger import Redemption, PointsTransaction, PointsLotAllocation
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding


class OverRedemptionDetector(BaseDetector):
    """
    Detector 2: Over-Redemption & FIFO Depletion Integrity (BR-04 / BR-08).
    Detects redemptions that exceed available positive balance, create unauthorized
    overdrafts, or lack supporting FIFO points lot allocations.
    Strictly distinguishes between genuine over-redemption and legitimate return-related
    negative balances (BR-10).
    """

    def __init__(self):
        super().__init__(
            detector_id="DET-OVER-REDEMPTION",
            category="OVER_REDEMPTION",
            name="Over-Redemption & Allocation Integrity Detector",
        )

    async def detect(
        self,
        db: AsyncSession,
        account_id: Optional[str] = None,
        **kwargs
    ) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        query = select(Redemption).options(
            selectinload(Redemption.transaction),
            selectinload(Redemption.allocations),
        )
        if account_id:
            query = query.where(Redemption.account_id == account_id)

        redemptions = (await db.execute(query)).scalars().all()

        for rdm in redemptions:
            tx = rdm.transaction
            if not tx:
                continue

            # Transaction points for redemptions are negative (-points_redeemed)
            pts_redeemed = rdm.points_redeemed
            running_bal_after = tx.running_balance
            available_before = running_bal_after - tx.points  # e.g., -1000 - (-1265) = 265

            # Total points allocated across points_lot_allocations
            total_allocated = sum(alloc.points_allocated for alloc in rdm.allocations)

            is_overdraft = (running_bal_after < 0)
            is_under_allocated = (total_allocated < pts_redeemed)

            if is_overdraft or is_under_allocated:
                overdraft_points = abs(running_bal_after) if is_overdraft else 0
                missing_allocation_points = max(0, pts_redeemed - total_allocated)
                variance = max(overdraft_points, missing_allocation_points)

                if is_overdraft:
                    severity = "CRITICAL"
                    severity_reason = (
                        f"CRITICAL financial liability: Redemption {rdm.redemption_id} requested {pts_redeemed} "
                        f"points against an available balance of {available_before} points, driving the account "
                        f"into an unauthorized negative running balance ({running_bal_after} pts). "
                        f"Violates BR-04 / BR-08."
                    )
                else:
                    severity = "HIGH"
                    severity_reason = (
                        f"HIGH allocation inconsistency: Redemption {rdm.redemption_id} redeemed {pts_redeemed} "
                        f"points but only {total_allocated} points were backed by points_lot_allocations. "
                        f"Unbacked points: {missing_allocation_points}."
                    )

                what_happened = (
                    f"Over-redemption detected on redemption {rdm.redemption_id} (transaction {tx.transaction_id}): "
                    f"requested {pts_redeemed} points against an available balance of {available_before} points, "
                    f"creating an unauthorized deficit of {variance} points."
                )

                description = (
                    f"Redemption {rdm.redemption_id} consumed {pts_redeemed} points, exceeding available balance "
                    f"({available_before} pts). Resulting running balance: {running_bal_after} pts. "
                    f"Allocated lot points: {total_allocated}/{pts_redeemed}."
                )

                recommendation = (
                    f"1. Immediately verify whether voucher code '{rdm.voucher_code}' has been redeemed with the merchant. "
                    f"2. Freeze loyalty account {rdm.account_id} pending audit review. "
                    f"3. Verify that optimistic/pessimistic concurrency locking (with_for_update) is operating on redemption requests."
                )

                finding = AnomalyFinding(
                    detector_id=self.detector_id,
                    category=self.category,
                    entity_type="REDEMPTION",
                    entity_id=rdm.redemption_id,
                    variance_amount=Decimal(str(variance)),
                    severity=severity,
                    severity_reason=severity_reason,
                    rule_violated="BR-04 / BR-08: Points Redemption Validation & FIFO Allocation (Redemption cannot exceed available positive balance)",
                    what_happened=what_happened,
                    description=description,
                    evidence={
                        "redemption_id": rdm.redemption_id,
                        "account_id": rdm.account_id,
                        "transaction_id": tx.transaction_id,
                        "reward_id": rdm.reward_id,
                        "voucher_code": rdm.voucher_code,
                        "requested_points": pts_redeemed,
                        "available_points_at_transaction_time": available_before,
                        "resulting_running_balance": running_bal_after,
                        "overdraft_points": overdraft_points,
                        "allocated_points": total_allocated,
                        "allocation_records_count": len(rdm.allocations),
                    },
                    discrepancy_calculation={
                        "formula": "requested_points - available_balance_at_transaction_time",
                        "requested_points": pts_redeemed,
                        "available_balance": available_before,
                        "overdraft_points": overdraft_points,
                        "unbacked_allocated_points": missing_allocation_points,
                    },
                    recommendation=recommendation,
                )
                findings.append(finding)

        return findings
