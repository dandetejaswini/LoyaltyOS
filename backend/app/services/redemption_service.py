import uuid
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import LoyaltyAccount
from backend.app.models.ledger import Reward, Redemption, PointsTransaction, PointsLot, PointsLotAllocation
from backend.app.schemas.ledger import RedemptionRequest, RedemptionResponse, RewardResponse, PointsLotAllocationResponse
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import NotFoundError, ConflictError, BadRequestError
from backend.app.core.logging import logger


class RedemptionService:
    """
    Workflow D: Concurrency-Safe Reward Redemption & FIFO Lot Allocation.
    Guarantees no over-redemption, row-level concurrency locking (with_for_update),
    FIFO breakage protection, and atomic ledger debit.
    """

    @classmethod
    async def list_available_rewards(cls, db: AsyncSession, active_only: bool = True) -> List[RewardResponse]:
        query = select(Reward)
        if active_only:
            query = query.where(Reward.is_active == True)
        query = query.order_by(asc(Reward.points_required))
        rewards = (await db.execute(query)).scalars().all()
        return [
            RewardResponse(
                reward_id=r.reward_id,
                name=r.name,
                reward_type=r.reward_type,
                points_required=r.points_required,
                monetary_value=r.monetary_value,
                stock_quantity=r.stock_quantity,
                is_active=r.is_active,
            )
            for r in rewards
        ]

    @classmethod
    async def redeem_reward(
        cls,
        db: AsyncSession,
        req: RedemptionRequest,
        actor_id: str,
    ) -> RedemptionResponse:
        # 1. Idempotency check
        tx_chk = select(PointsTransaction).where(PointsTransaction.idempotency_key == req.idempotency_key)
        if (await db.execute(tx_chk)).scalar_one_or_none():
            raise ConflictError(detail=f"Redemption with idempotency key '{req.idempotency_key}' was already processed.")

        # 2. Concurrency-Safe Account Retrieval (SELECT FOR UPDATE)
        acc_stmt = select(LoyaltyAccount).where(LoyaltyAccount.account_id == req.account_id).with_for_update()
        account = (await db.execute(acc_stmt)).scalar_one_or_none()
        if not account:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                operation_type="REDEMPTION",
                error_code="ACCOUNT_NOT_FOUND",
                error_message=f"Loyalty account '{req.account_id}' does not exist.",
                payload={"account_id": req.account_id, "idempotency_key": req.idempotency_key}
            )
            await db.commit()
            raise NotFoundError(detail=f"Loyalty account '{req.account_id}' not found.")

        # 3. Check Account Status and Negative Balance (BR-08 / BR-10 Freeze)
        if account.status != "ACTIVE":
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="ACCOUNT_FROZEN",
                error_message=f"Account status is '{account.status}'. Redemptions are prohibited.",
                payload={"account_id": req.account_id, "status": account.status}
            )
            await db.commit()
            raise BadRequestError(detail=f"Account is in '{account.status}' status. Redemptions are frozen.")

        if account.current_balance < 0:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="NEGATIVE_BALANCE_FROZEN",
                error_message=f"Account balance is negative ({account.current_balance}). Redemptions are frozen until liability is cleared.",
                payload={"account_id": req.account_id, "current_balance": account.current_balance}
            )
            await db.commit()
            raise BadRequestError(detail="Account balance is negative. Redemptions are frozen until liability is cleared.")

        # 4. Reward Validation
        rew_stmt = select(Reward).where(Reward.reward_id == req.reward_id)
        reward = (await db.execute(rew_stmt)).scalar_one_or_none()
        if not reward or not reward.is_active:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="REWARD_UNAVAILABLE",
                error_message=f"Reward '{req.reward_id}' is invalid or inactive.",
                payload={"reward_id": req.reward_id}
            )
            await db.commit()
            raise NotFoundError(detail=f"Reward '{req.reward_id}' is not available.")

        # Check Stock if tracked
        if reward.stock_quantity is not None and reward.stock_quantity <= 0:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="OUT_OF_STOCK",
                error_message=f"Reward '{reward.name}' is out of stock.",
                payload={"reward_id": req.reward_id}
            )
            await db.commit()
            raise BadRequestError(detail=f"Reward '{reward.name}' is out of stock.")

        # 5. Sufficient Balance Check (BR-08: No Over-Redemption)
        points_needed = reward.points_required
        if account.current_balance < points_needed:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="INSUFFICIENT_BALANCE",
                error_message=f"Insufficient points. Required: {points_needed}, Available: {account.current_balance}.",
                payload={
                    "account_id": account.account_id,
                    "points_required": points_needed,
                    "available_balance": account.current_balance,
                }
            )
            await db.commit()
            raise BadRequestError(
                detail=f"Insufficient points balance ({account.current_balance} available, {points_needed} required)."
            )

        # 6. FIFO Points Lot Allocation
        # Query active lots sorted by expires_at ASC, created_at ASC with lock
        lots_stmt = (
            select(PointsLot)
            .where(
                PointsLot.account_id == account.account_id,
                PointsLot.remaining_points > 0,
                PointsLot.status.in_(["ACTIVE", "PARTIALLY_REDEEMED"]),
            )
            .order_by(asc(PointsLot.expires_at), asc(PointsLot.created_at))
            .with_for_update()
        )
        active_lots = (await db.execute(lots_stmt)).scalars().all()

        total_active_points = sum(l.remaining_points for l in active_lots)
        if total_active_points < points_needed:
            # Discrepancy between stored balance and unexpired lots
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                account_id=account.account_id,
                operation_type="REDEMPTION",
                error_code="ACTIVE_LOTS_EXHAUSTED",
                error_message=f"Unexpired active lot points ({total_active_points}) < required points ({points_needed}).",
                payload={"active_lot_points": total_active_points, "points_needed": points_needed}
            )
            await db.commit()
            raise BadRequestError(detail="Insufficient unexpired active points available for redemption.")

        now = datetime.now(timezone.utc)
        rdm_id = f"RDM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        tx_id = f"PTS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        voucher_code = f"VOUCH-{uuid.uuid4().hex[:4].upper()}-{random.randint(100000, 999999)}"

        # 7. Greedily Allocate Points from FIFO Lots
        allocated_so_far = 0
        lot_allocations: List[PointsLotAllocation] = []

        for lot in active_lots:
            if allocated_so_far >= points_needed:
                break

            take = min(lot.remaining_points, points_needed - allocated_so_far)
            lot.remaining_points -= take
            allocated_so_far += take
            lot.status = "EXHAUSTED" if lot.remaining_points == 0 else "PARTIALLY_REDEEMED"
            lot.updated_at = now

            alloc = PointsLotAllocation(
                allocation_id=f"ALL-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
                lot_id=lot.lot_id,
                redemption_id=rdm_id,
                transaction_id=tx_id,
                points_allocated=take,
                created_at=now,
            )
            db.add(alloc)
            lot_allocations.append(alloc)

        # 8. Append-Only Points Transaction (Debit)
        new_balance = account.current_balance - points_needed
        debit_tx = PointsTransaction(
            transaction_id=tx_id,
            account_id=account.account_id,
            order_id=None,
            related_transaction_id=None,
            rule_id=None,
            entry_type="REDEMPTION",
            points=-points_needed,
            running_balance=new_balance,
            idempotency_key=req.idempotency_key,
            notes=f"Redeemed reward '{reward.name}' ({points_needed} points) voucher={voucher_code}",
            created_at=now,
        )
        db.add(debit_tx)

        # 9. Create Redemption Record
        voucher_expires_at = now + timedelta(days=90)
        redemption = Redemption(
            redemption_id=rdm_id,
            account_id=account.account_id,
            reward_id=reward.reward_id,
            transaction_id=tx_id,
            points_redeemed=points_needed,
            voucher_code=voucher_code,
            status="ISSUED",
            created_at=now,
            expires_at=voucher_expires_at,
        )
        db.add(redemption)

        # 10. Update Account Balance
        account.current_balance = new_balance
        account.lifetime_redeemed += points_needed
        account.updated_at = now

        # Update Reward stock if tracked
        if reward.stock_quantity is not None:
            reward.stock_quantity -= 1

        # 11. Audit Trail
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="REWARD_REDEEMED",
            entity_type="redemptions",
            entity_id=rdm_id,
            metadata={
                "account_id": account.account_id,
                "reward_id": reward.reward_id,
                "reward_name": reward.name,
                "points_redeemed": points_needed,
                "new_balance": new_balance,
                "voucher_code": voucher_code,
                "transaction_id": tx_id,
                "lots_consumed_count": len(lot_allocations),
            }
        )

        await db.commit()

        return RedemptionResponse(
            redemption_id=rdm_id,
            account_id=account.account_id,
            reward_id=reward.reward_id,
            reward_name=reward.name,
            points_redeemed=points_needed,
            voucher_code=voucher_code,
            status="ISSUED",
            transaction_id=tx_id,
            new_balance=new_balance,
            allocations=[
                PointsLotAllocationResponse(
                    allocation_id=a.allocation_id,
                    lot_id=a.lot_id,
                    redemption_id=a.redemption_id,
                    transaction_id=a.transaction_id,
                    points_allocated=a.points_allocated,
                    created_at=a.created_at,
                )
                for a in lot_allocations
            ],
            created_at=now,
            expires_at=voucher_expires_at,
        )
