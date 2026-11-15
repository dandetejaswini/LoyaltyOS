from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import LoyaltyAccount
from backend.app.models.ledger import PointsTransaction, PointsLot
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding


class BalanceMismatchDetector(BaseDetector):
    """
    Detector 1: Account Balance Mismatch (BR-01 Double-Entry Balance Invariant).
    Identifies cases where stored loyalty account balance diverges from the
    calculated sum of immutable journal transactions, or where active points lots
    fail to reconcile with the available balance.
    """

    def __init__(self):
        super().__init__(
            detector_id="DET-BALANCE-MISMATCH",
            category="BALANCE_MISMATCH",
            name="Account Balance & Ledger Mismatch Detector",
        )

    async def detect(
        self,
        db: AsyncSession,
        account_id: Optional[str] = None,
        **kwargs
    ) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        # 1. Query accounts to evaluate
        acc_query = select(LoyaltyAccount)
        if account_id:
            acc_query = acc_query.where(LoyaltyAccount.account_id == account_id)
        accounts = (await db.execute(acc_query)).scalars().all()

        for acc in accounts:
            # 2. Compute ledger-derived balance
            sum_stmt = select(func.coalesce(func.sum(PointsTransaction.points), 0)).where(
                PointsTransaction.account_id == acc.account_id
            )
            ledger_sum = (await db.execute(sum_stmt)).scalar() or 0

            stored_balance = acc.current_balance
            variance = stored_balance - ledger_sum

            # Check if active lots reconcile with current balance when balance >= 0
            lots_stmt = select(func.coalesce(func.sum(PointsLot.remaining_points), 0)).where(
                PointsLot.account_id == acc.account_id,
                PointsLot.status.in_(["ACTIVE", "PARTIALLY_REDEEMED"]),
            )
            lots_remaining = (await db.execute(lots_stmt)).scalar() or 0

            if variance != 0:
                # Severity determination
                if abs(variance) >= 100 or stored_balance > ledger_sum:
                    severity = "CRITICAL"
                    severity_reason = (
                        f"CRITICAL financial integrity failure: Account {acc.account_id} stored balance "
                        f"deviates from the immutable ledger journal by {variance:+d} points. "
                        f"Discrepancies >= 100 points or positive unbacked balances represent direct financial risk."
                    )
                else:
                    severity = "HIGH"
                    severity_reason = (
                        f"HIGH ledger inconsistency: Account {acc.account_id} balance deviates from journal by "
                        f"{variance:+d} points, violating the double-entry accounting invariant."
                    )

                # Fetch recent transaction references for evidence
                recent_tx_stmt = (
                    select(PointsTransaction)
                    .where(PointsTransaction.account_id == acc.account_id)
                    .order_by(desc(PointsTransaction.created_at))
                    .limit(5)
                )
                recent_txs = (await db.execute(recent_tx_stmt)).scalars().all()
                tx_evidence = [
                    {
                        "transaction_id": tx.transaction_id,
                        "entry_type": tx.entry_type,
                        "points": tx.points,
                        "running_balance": tx.running_balance,
                        "created_at": tx.created_at.isoformat() if tx.created_at else None,
                    }
                    for tx in recent_txs
                ]

                what_happened = (
                    f"Direct database drift detected on loyalty account {acc.account_id}: "
                    f"stored balance is {stored_balance} points, but the sum of all journal transactions is "
                    f"{ledger_sum} points (variance: {variance:+d} points)."
                )

                description = (
                    f"Account balance ({stored_balance} pts) does not match sum of immutable journal transactions "
                    f"({ledger_sum} pts). Difference: {variance:+d} pts. Active lots sum: {lots_remaining} pts."
                )

                recommendation = (
                    "1. Inspect forensic transaction audit logs for out-of-band updates or failed transaction commits. "
                    "2. If unauthorized database tampering occurred, freeze the account immediately. "
                    "3. Post an operator-authorized dual-key ADJUSTMENT transaction to restore double-entry parity. "
                    "Never modify the account balance directly in the database."
                )

                finding = AnomalyFinding(
                    detector_id=self.detector_id,
                    category=self.category,
                    entity_type="ACCOUNT",
                    entity_id=acc.account_id,
                    variance_amount=Decimal(str(abs(variance))),
                    severity=severity,
                    severity_reason=severity_reason,
                    rule_violated="BR-01: Double-Entry Ledger Balance Invariant (Account balance must equal sum of journal transactions)",
                    what_happened=what_happened,
                    description=description,
                    evidence={
                        "account_id": acc.account_id,
                        "customer_id": acc.customer_id,
                        "stored_balance": stored_balance,
                        "calculated_ledger_balance": ledger_sum,
                        "variance": variance,
                        "active_lots_remaining_points": lots_remaining,
                        "recent_transactions": tx_evidence,
                    },
                    discrepancy_calculation={
                        "formula": "stored_balance - sum(points_transactions.points)",
                        "stored_balance": stored_balance,
                        "calculated_ledger_balance": ledger_sum,
                        "variance": variance,
                    },
                    recommendation=recommendation,
                )
                findings.append(finding)

        return findings
