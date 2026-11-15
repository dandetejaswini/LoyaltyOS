from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.app.models.ledger import PointsLot, ExpiryBatchItem, PointsTransaction
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding


class DoubleExpiryDetector(BaseDetector):
    """
    Detector 4: Duplicate & Double Expiry (BR-05 / BR-11).
    Detects cases where a points lot was expired more than once, processed in multiple
    expiry batches, or had more points deducted than its initial points balance.
    Protects customer equity against non-idempotent batch execution.
    """

    def __init__(self):
        super().__init__(
            detector_id="DET-DOUBLE-EXPIRY",
            category="DOUBLE_EXPIRY",
            name="Points Expiry Idempotency & Double Deduction Detector",
        )

    async def detect(
        self,
        db: AsyncSession,
        account_id: Optional[str] = None,
        **kwargs
    ) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        # 1. Query lots that have been processed in expiry batches
        # Group expiry batch items by lot_id
        items_query = select(ExpiryBatchItem)
        all_items = (await db.execute(items_query)).scalars().all()

        items_by_lot: Dict[str, List[ExpiryBatchItem]] = {}
        for item in all_items:
            items_by_lot.setdefault(item.lot_id, []).append(item)

        # 2. Inspect lots with multiple expiry batch items or examine each lot
        for lot_id, batch_items in items_by_lot.items():
            # Query lot details
            lot_stmt = select(PointsLot).where(PointsLot.lot_id == lot_id)
            if account_id:
                lot_stmt = lot_stmt.where(PointsLot.account_id == account_id)
            lot = (await db.execute(lot_stmt)).scalar_one_or_none()
            if not lot:
                continue

            total_batch_items = len(batch_items)
            total_points_expired = sum(item.points_expired for item in batch_items)
            expected_expiry_points = lot.initial_points

            # Check for double expiry anomaly
            is_multiple_items = (total_batch_items > 1)
            is_excess_deducted = (total_points_expired > expected_expiry_points)

            if is_multiple_items or is_excess_deducted:
                excess_points = max(0, total_points_expired - expected_expiry_points)
                if excess_points == 0 and is_multiple_items:
                    # If multiple items deducted points, excess is the sum of subsequent deductions
                    excess_points = sum(item.points_expired for item in batch_items[1:])

                batch_ids = list(set(item.batch_id for item in batch_items))
                tx_ids = [item.transaction_id for item in batch_items]

                if excess_points > 0:
                    severity = "HIGH"
                    severity_reason = (
                        f"HIGH customer financial impact: Points lot {lot.lot_id} was subjected to multiple "
                        f"expiry deductions across batches {batch_ids}, stripping {excess_points} excess points "
                        f"from account {lot.account_id}. Violates BR-05 / BR-11 (Expiry Idempotency)."
                    )
                else:
                    severity = "MEDIUM"
                    severity_reason = (
                        f"MEDIUM batch consistency issue: Points lot {lot.lot_id} was referenced in "
                        f"{total_batch_items} expiry batch records without excess point variance."
                    )

                what_happened = (
                    f"Double expiry detected on lot {lot.lot_id} (account {lot.account_id}): "
                    f"lot was processed across {total_batch_items} expiry batches ({', '.join(batch_ids)}), "
                    f"resulting in {total_points_expired} total points deducted against an initial lot size "
                    f"of {lot.initial_points} points (excess deduction: {excess_points} pts)."
                )

                description = (
                    f"Lot {lot.lot_id}: Processed in batches {batch_ids}. "
                    f"Initial points: {lot.initial_points}. Total points expired: {total_points_expired}. "
                    f"Excess points confiscated: {excess_points}."
                )

                recommendation = (
                    f"1. Check the idempotency lock and scheduling configuration of the batch expiry worker. "
                    f"2. Post an operator-approved ADJUSTMENT_CREDIT transaction of {excess_points} points to "
                    f"account {lot.account_id} to restore wrongfully confiscated customer points."
                )

                finding = AnomalyFinding(
                    detector_id=self.detector_id,
                    category=self.category,
                    entity_type="POINTS_LOT",
                    entity_id=lot.lot_id,
                    variance_amount=Decimal(str(excess_points if excess_points > 0 else total_points_expired)),
                    severity=severity,
                    severity_reason=severity_reason,
                    rule_violated="BR-05 / BR-11: Points Expiry Idempotency (Expired lots cannot be processed a second time)",
                    what_happened=what_happened,
                    description=description,
                    evidence={
                        "lot_id": lot.lot_id,
                        "account_id": lot.account_id,
                        "initial_points": lot.initial_points,
                        "remaining_points": lot.remaining_points,
                        "status": lot.status,
                        "expiry_batch_count": total_batch_items,
                        "batch_ids": batch_ids,
                        "expiry_batch_item_ids": [item.item_id for item in batch_items],
                        "transaction_ids": tx_ids,
                        "total_points_expired": total_points_expired,
                        "excess_points_deducted": excess_points,
                    },
                    discrepancy_calculation={
                        "formula": "total_points_expired_in_batches - initial_lot_points",
                        "total_points_expired": total_points_expired,
                        "initial_lot_points": lot.initial_points,
                        "excess_points": excess_points,
                    },
                    recommendation=recommendation,
                )
                findings.append(finding)

        return findings
