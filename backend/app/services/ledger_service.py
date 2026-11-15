import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import LoyaltyAccount, Customer
from backend.app.models.ledger import PointsTransaction, PointsLot
from backend.app.schemas.ledger import (
    PointsTransactionResponse,
    TransactionHistoryPage,
    PointsLotResponse,
    ReconciliationReport,
)
from backend.app.core.errors import NotFoundError


class LedgerService:
    """
    Workflow C: Balance and Ledger Reconciliation.
    Treats the append-only journal (points_transactions) as the financial source of truth.
    Provides auditable reconciliation against stored account balance without silent mutations.
    """

    @classmethod
    async def get_transaction_history(
        cls,
        db: AsyncSession,
        account_id: str,
        page: int = 1,
        page_size: int = 20,
        entry_type: Optional[str] = None,
    ) -> TransactionHistoryPage:
        # Verify account exists
        acc_stmt = select(LoyaltyAccount).where(LoyaltyAccount.account_id == account_id)
        acc_res = await db.execute(acc_stmt)
        if not acc_res.scalar_one_or_none():
            raise NotFoundError(detail=f"Loyalty account '{account_id}' not found.")

        # Base query
        query = select(PointsTransaction).where(PointsTransaction.account_id == account_id)
        if entry_type:
            query = query.where(PointsTransaction.entry_type == entry_type.upper().strip())

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Paginate (Order by created_at DESC, transaction_id DESC)
        offset = (page - 1) * page_size
        paged_query = query.order_by(desc(PointsTransaction.created_at), desc(PointsTransaction.transaction_id)).offset(offset).limit(page_size)
        tx_records = (await db.execute(paged_query)).scalars().all()

        items = [
            PointsTransactionResponse(
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                order_id=tx.order_id,
                related_transaction_id=tx.related_transaction_id,
                rule_id=tx.rule_id,
                entry_type=tx.entry_type,
                direction="CREDIT" if tx.points > 0 else "DEBIT",
                points=tx.points,
                running_balance=tx.running_balance,
                idempotency_key=tx.idempotency_key,
                notes=tx.notes,
                created_at=tx.created_at,
            )
            for tx in tx_records
        ]

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return TransactionHistoryPage(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    async def get_account_lots(
        cls,
        db: AsyncSession,
        account_id: str,
        status: Optional[str] = None,
    ) -> List[PointsLotResponse]:
        query = select(PointsLot).where(PointsLot.account_id == account_id)
        if status:
            query = query.where(PointsLot.status == status.upper().strip())
        query = query.order_by(asc(PointsLot.expires_at), asc(PointsLot.created_at))

        lots = (await db.execute(query)).scalars().all()
        return [
            PointsLotResponse(
                lot_id=l.lot_id,
                transaction_id=l.transaction_id,
                account_id=l.account_id,
                initial_points=l.initial_points,
                remaining_points=l.remaining_points,
                status=l.status,
                expires_at=l.expires_at,
                created_at=l.created_at,
                updated_at=l.updated_at,
            )
            for l in lots
        ]

    @classmethod
    async def reconcile_account_balance(
        cls,
        db: AsyncSession,
        account_id: str,
    ) -> ReconciliationReport:
        """
        Reconciles stored balance against the sum of journal transactions.
        Identifies multi-point balance drift without silent correction.
        """
        acc_stmt = select(LoyaltyAccount).where(LoyaltyAccount.account_id == account_id)
        acc_res = await db.execute(acc_stmt)
        account = acc_res.scalar_one_or_none()
        if not account:
            raise NotFoundError(detail=f"Loyalty account '{account_id}' not found.")

        # Compute sum of journal transactions
        sum_stmt = select(func.coalesce(func.sum(PointsTransaction.points), 0)).where(PointsTransaction.account_id == account_id)
        ledger_derived_balance = (await db.execute(sum_stmt)).scalar() or 0

        # Breakdown by entry_type
        breakdown_stmt = (
            select(PointsTransaction.entry_type, func.coalesce(func.sum(PointsTransaction.points), 0))
            .where(PointsTransaction.account_id == account_id)
            .group_by(PointsTransaction.entry_type)
        )
        breakdown_rows = (await db.execute(breakdown_stmt)).all()
        breakdown = {row[0]: row[1] for row in breakdown_rows}

        stored_balance = account.current_balance
        discrepancy = stored_balance - ledger_derived_balance
        is_reconciled = (discrepancy == 0)

        return ReconciliationReport(
            account_id=account.account_id,
            customer_id=account.customer_id,
            stored_balance=stored_balance,
            ledger_derived_balance=ledger_derived_balance,
            discrepancy_amount=discrepancy,
            is_reconciled=is_reconciled,
            status="RECONCILED" if is_reconciled else "DISCREPANCY_DETECTED",
            breakdown=breakdown,
            evaluation_time=datetime.now(timezone.utc),
        )
