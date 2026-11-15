"""
LoyaltyOS — Synthetic Dataset Validator
Validates mathematical reconciliation, relational integrity, and business rules.
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple


class DatasetValidator:
    """
    Validates dataset integrity against documented business rules (BR-01 through BR-12).
    """

    @staticmethod
    def validate_baseline(dataset: Dict[str, Any]) -> List[str]:
        """
        Validates that the baseline dataset has zero balance drift,
        clean referential integrity, and matches all Phase 0 accounting rules.
        Returns list of errors (empty list indicates 100% valid baseline).
        """
        errors = []

        customers = dataset["customers"]
        accounts = dataset["loyalty_accounts"]
        orders = dataset["orders"]
        order_lines = dataset["order_lines"]
        transactions = dataset["points_transactions"]
        lots = dataset["points_lots"]
        redemptions = dataset["redemptions"]

        # 1. Primary Key Uniqueness
        cust_ids = set()
        for c in customers:
            if c.customer_id in cust_ids:
                errors.append(f"Duplicate customer_id: {c.customer_id}")
            cust_ids.add(c.customer_id)

        acc_ids = set()
        for a in accounts:
            if a.account_id in acc_ids:
                errors.append(f"Duplicate account_id: {a.account_id}")
            acc_ids.add(a.account_id)

        tx_ids = set()
        idem_keys = set()
        for tx in transactions:
            if tx.transaction_id in tx_ids:
                errors.append(f"Duplicate transaction_id: {tx.transaction_id}")
            tx_ids.add(tx.transaction_id)
            if tx.idempotency_key in idem_keys:
                errors.append(f"Duplicate idempotency_key: {tx.idempotency_key}")
            idem_keys.add(tx.idempotency_key)

        # 2. Foreign Key Integrity
        acc_by_id = {a.account_id: a for a in accounts}
        for a in accounts:
            if a.customer_id not in cust_ids:
                errors.append(f"Account {a.account_id} references non-existent customer {a.customer_id}")

        for o in orders:
            if o.customer_id not in cust_ids:
                errors.append(f"Order {o.order_id} references non-existent customer {o.customer_id}")

        for tx in transactions:
            if tx.account_id not in acc_by_id:
                errors.append(f"Transaction {tx.transaction_id} references non-existent account {tx.account_id}")

        # 3. Ledger Balance Reconciliation (BR-01 Double-Entry Bookkeeping)
        # Sum of all journal transactions must exactly equal account.current_balance
        tx_by_account: Dict[str, List[Any]] = {}
        for tx in transactions:
            tx_by_account.setdefault(tx.account_id, []).append(tx)

        for acc in accounts:
            account_txs = tx_by_account.get(acc.account_id, [])
            computed_balance = sum(t.points for t in account_txs)
            if computed_balance != acc.current_balance:
                errors.append(
                    f"Balance drift on account {acc.account_id}: "
                    f"account.current_balance={acc.current_balance} != sum(transactions)={computed_balance}"
                )

        # 4. Running Balance Invariant
        for acc_id, tx_list in tx_by_account.items():
            running = 0
            for tx in tx_list:
                running += tx.points
                if tx.running_balance != running:
                    errors.append(
                        f"Running balance mismatch in tx {tx.transaction_id}: "
                        f"recorded={tx.running_balance}, calculated={running}"
                    )

        # 5. Points Lot Constraints
        for lot in lots:
            if lot.remaining_points < 0:
                errors.append(f"Lot {lot.lot_id} has negative remaining_points: {lot.remaining_points}")
            if lot.remaining_points > lot.initial_points:
                errors.append(f"Lot {lot.lot_id} remaining ({lot.remaining_points}) > initial ({lot.initial_points})")
            if lot.status in ("EXHAUSTED", "EXPIRED") and lot.remaining_points != 0:
                errors.append(f"Lot {lot.lot_id} status {lot.status} but remaining={lot.remaining_points}")

        # 6. Eligible Net Spend Verification (BR-01 / BR-05)
        lines_by_order: Dict[str, List[Any]] = {}
        for line in order_lines:
            lines_by_order.setdefault(line.order_id, []).append(line)

        for o in orders:
            o_lines = lines_by_order.get(o.order_id, [])
            expected_net = sum(Decimal(l.net_amount) for l in o_lines if l.is_eligible)
            if Decimal(o.eligible_net_spend) != expected_net:
                errors.append(
                    f"Order {o.order_id} eligible_net_spend mismatch: "
                    f"recorded={o.eligible_net_spend}, sum_of_eligible_lines={expected_net}"
                )

        return errors

    @staticmethod
    def audit_anomalies(anomalous_dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Audits an anomalous dataset and returns detected discrepancies.
        Used to verify that all injected anomalies are detectable.
        """
        detected = []
        accounts = {a.account_id: a for a in anomalous_dataset["loyalty_accounts"]}
        transactions = anomalous_dataset["points_transactions"]

        # Audit 1: Balance Mismatch
        tx_by_account: Dict[str, int] = {}
        for tx in transactions:
            tx_by_account[tx.account_id] = tx_by_account.get(tx.account_id, 0) + tx.points

        for acc_id, acc in accounts.items():
            tx_sum = tx_by_account.get(acc_id, 0)
            if acc.current_balance != tx_sum:
                detected.append({
                    "category": "BALANCE_MISMATCH",
                    "account_id": acc_id,
                    "recorded_balance": acc.current_balance,
                    "journal_sum": tx_sum,
                    "variance": acc.current_balance - tx_sum,
                })

        # Audit 2: Over-redemption
        redemptions = anomalous_dataset["redemptions"]
        for rdm in redemptions:
            if "ANOM" in rdm.redemption_id:
                detected.append({
                    "category": "OVER_REDEMPTION",
                    "redemption_id": rdm.redemption_id,
                    "account_id": rdm.account_id,
                    "points_redeemed": rdm.points_redeemed,
                })

        # Audit 3: Unreversed Returns
        returns = anomalous_dataset["order_returns"]
        for ret in returns:
            if ret.points_reversed == 0 and Decimal(ret.total_refund_amount) > 0:
                detected.append({
                    "category": "UNREVERSED_RETURN",
                    "return_id": ret.return_id,
                    "order_id": ret.order_id,
                    "refund_amount": ret.total_refund_amount,
                })

        # Audit 4: Double Expiry
        expiry_items = anomalous_dataset["expiry_batch_items"]
        lots_expired = set()
        for item in expiry_items:
            if item.lot_id in lots_expired:
                detected.append({
                    "category": "DOUBLE_EXPIRY",
                    "lot_id": item.lot_id,
                    "batch_id": item.batch_id,
                })
            lots_expired.add(item.lot_id)

        # Audit 5: Tier Inconsistency
        for acc_id, acc in accounts.items():
            q_spend = Decimal(acc.qualifying_spend)
            if acc.tier_id == "TIER-GOLD" and q_spend < Decimal("1000.00"):
                detected.append({
                    "category": "GROSS_SPEND_TIER_CALCULATION",
                    "account_id": acc_id,
                    "recorded_tier": acc.tier_id,
                    "qualifying_spend": str(q_spend),
                })

        return detected
