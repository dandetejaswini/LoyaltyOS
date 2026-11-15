from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_customer
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer, LoyaltyAccount
from backend.app.schemas.ledger import (
    TransactionHistoryPage,
    PointsLotResponse,
    ReconciliationReport,
)
from backend.app.services.ledger_service import LedgerService
from backend.app.services.customer_service import CustomerService
from backend.app.core.errors import ForbiddenError
from sqlalchemy import select

router = APIRouter(prefix="/ledger", tags=["Points Ledger & Balance Reconciliation"])


async def verify_account_ownership(db: AsyncSession, current_user: AppUser, account_id: str):
    """Enforces that customers can only query their own ledger data."""
    if current_user.role == "CUSTOMER":
        account = await CustomerService.get_account(db, account_id)
        stmt = select(Customer).where(Customer.user_id == current_user.id)
        cust = (await db.execute(stmt)).scalar_one_or_none()
        if not cust or cust.customer_id != account.customer_id:
            raise ForbiddenError(detail="Access denied: You may only view your own ledger data.")


@router.get("/accounts/{account_id}/history", response_model=TransactionHistoryPage)
async def get_transaction_history(
    account_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    entry_type: Optional[str] = Query(None, description="Filter by entry_type (e.g. ACCRUAL, REDEMPTION, REVERSAL, EXPIRY)"),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow C: Points Transaction Journal History.
    Returns immutable ledger transactions with running balance and credit/debit classification.
    """
    await verify_account_ownership(db, current_user, account_id)
    return await LedgerService.get_transaction_history(
        db=db,
        account_id=account_id,
        page=page,
        page_size=page_size,
        entry_type=entry_type,
    )


@router.get("/accounts/{account_id}/lots", response_model=List[PointsLotResponse])
async def get_points_lots(
    account_id: str,
    status: Optional[str] = Query(None, description="Filter by lot status (ACTIVE, PARTIALLY_REDEEMED, EXHAUSTED, EXPIRED)"),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Retrieves points lot inventory tracked for FIFO consumption and batch expiration.
    """
    await verify_account_ownership(db, current_user, account_id)
    return await LedgerService.get_account_lots(
        db=db,
        account_id=account_id,
        status=status,
    )


@router.get("/accounts/{account_id}/reconciliation", response_model=ReconciliationReport)
async def reconcile_account_balance(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Workflow C: Balance & Ledger Double-Entry Reconciliation (BR-01).
    Compares stored current_balance against the sum of append-only transactions.
    Transparently reports discrepancy without silent data corruption.
    """
    await verify_account_ownership(db, current_user, account_id)
    return await LedgerService.reconcile_account_balance(
        db=db,
        account_id=account_id,
    )
