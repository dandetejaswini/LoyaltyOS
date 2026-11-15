import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import LoyaltyAccount
from backend.app.models.ledger import PointsLot, PointsTransaction, ExpiryBatch, ExpiryBatchItem
from backend.app.schemas.ledger import ExpiryExecutionRequest, ExpiryBatchResponse
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import ConflictError
from backend.app.core.logging import logger


class ExpiryService:
    """
    Workflow F: Idempotent Points Lot Expiration Service.
    Identifies lots past 365-day expiration, atomically creates expiry batches and items,
    appends expiry debit transactions, and updates account balances without double-deduction.
    """

    @classmethod
    async def process_expiries(
        cls,
        db: AsyncSession,
        req: ExpiryExecutionRequest,
        actor_id: str,
    ) -> ExpiryBatchResponse:
        # 1. Idempotency check on batch
        batch_chk = select(ExpiryBatch).where(ExpiryBatch.batch_id == req.idempotency_key)
        existing_batch = (await db.execute(batch_chk)).scalar_one_or_none()
        if existing_batch:
            raise ConflictError(detail=f"Expiry batch with ID/key '{req.idempotency_key}' was already executed.")

        cutoff = req.cutoff_date or datetime.now(timezone.utc)
        batch_id = req.idempotency_key

        # 2. Identify all expired lots with positive remaining points
        lots_stmt = (
            select(PointsLot)
            .where(
                PointsLot.expires_at <= cutoff,
                PointsLot.remaining_points > 0,
                PointsLot.status.in_(["ACTIVE", "PARTIALLY_REDEEMED"]),
            )
            .order_by(asc(PointsLot.expires_at))
            .with_for_update()
        )
        expired_lots = (await db.execute(lots_stmt)).scalars().all()

        now = datetime.now(timezone.utc)
        total_pts_expired = 0
        batch_items: List[ExpiryBatchItem] = []

        # Create Expiry Batch Header
        batch = ExpiryBatch(
            batch_id=batch_id,
            cutoff_date=cutoff,
            total_lots_processed=len(expired_lots),
            total_points_expired=0,  # Updated after aggregation
            status="IN_PROGRESS",
            created_at=now,
        )
        db.add(batch)
        await db.flush()

        # Cache accounts to update balances
        account_ids = list({l.account_id for l in expired_lots})
        accounts_stmt = select(LoyaltyAccount).where(LoyaltyAccount.account_id.in_(account_ids)).with_for_update()
        accounts_map = {a.account_id: a for a in (await db.execute(accounts_stmt)).scalars().all()}

        for lot in expired_lots:
            pts_to_expire = lot.remaining_points
            if pts_to_expire <= 0:
                continue

            total_pts_expired += pts_to_expire
            account = accounts_map.get(lot.account_id)

            item_id = f"EXP-ITEM-{batch_id}-{len(batch_items) + 1:04d}"
            tx_id = f"PTS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

            # Create Expiry Batch Item
            batch_item = ExpiryBatchItem(
                item_id=item_id,
                batch_id=batch_id,
                lot_id=lot.lot_id,
                transaction_id=tx_id,
                points_expired=pts_to_expire,
                created_at=now,
            )
            db.add(batch_item)
            batch_items.append(batch_item)

            # Update Lot Status
            lot.remaining_points = 0
            lot.status = "EXPIRED"
            lot.updated_at = now

            if account:
                new_balance = account.current_balance - pts_to_expire
                # Append Points Transaction (Debit)
                expiry_tx = PointsTransaction(
                    transaction_id=tx_id,
                    account_id=account.account_id,
                    order_id=None,
                    related_transaction_id=lot.transaction_id,
                    rule_id=None,
                    entry_type="EXPIRY",
                    points=-pts_to_expire,
                    running_balance=new_balance,
                    idempotency_key=f"IDEM-EXP-{lot.lot_id}-{batch_id}",
                    notes=f"Expired lot {lot.lot_id} in batch {batch_id}",
                    created_at=now,
                )
                db.add(expiry_tx)

                # Update Account Balance
                account.current_balance = new_balance
                account.updated_at = now

        # Finalize Batch
        batch.total_points_expired = total_pts_expired
        batch.status = "COMPLETED"

        # Audit Trail
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="EXPIRY_BATCH_COMPLETED",
            entity_type="expiry_batches",
            entity_id=batch_id,
            metadata={
                "cutoff_date": cutoff.isoformat(),
                "total_lots_processed": len(expired_lots),
                "total_points_expired": total_pts_expired,
            }
        )

        await db.commit()

        return ExpiryBatchResponse(
            batch_id=batch_id,
            cutoff_date=cutoff,
            total_lots_processed=len(expired_lots),
            total_points_expired=total_pts_expired,
            status="COMPLETED",
            items_count=len(batch_items),
            created_at=now,
        )
