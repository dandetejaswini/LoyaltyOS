"""
LoyaltyOS — Controlled Anomaly Injector
Injects 5 designated forensic anomaly categories into a copy of the baseline dataset,
generating an isolated ground-truth anomaly manifest.
"""

import copy
import random
from decimal import Decimal
from typing import Dict, Any, List, Tuple

from backend.app.seed.models import (
    InjectedAnomaly,
    SyntheticPointsTransaction,
    SyntheticOrderReturn,
    SyntheticExpiryBatch,
    SyntheticExpiryBatchItem,
    SyntheticRedemption,
)


class AnomalyInjector:
    """
    Injects deterministic anomalies across 5 categories:
    1. BALANCE_MISMATCH
    2. OVER_REDEMPTION
    3. UNREVERSED_RETURN
    4. DOUBLE_EXPIRY
    5. GROSS_SPEND_TIER_CALCULATION
    """

    def __init__(self, seed: int = 20261022):
        self.rng = random.Random(seed + 999)
        self.anomalies: List[InjectedAnomaly] = []
        self._anomaly_counter = 0

    def inject_anomalies(self, baseline_dataset: Dict[str, Any]) -> Tuple[Dict[str, Any], List[InjectedAnomaly]]:
        """
        Creates an isolated deep-copy of the baseline dataset and injects controlled anomalies.
        Returns (anomalous_dataset, ground_truth_anomalies).
        """
        dataset = copy.deepcopy(baseline_dataset)
        self.anomalies = []
        self._anomaly_counter = 0

        # Inject each of the 5 categories deterministically
        self._inject_balance_mismatch(dataset)
        self._inject_over_redemption(dataset)
        self._inject_unreversed_return(dataset)
        self._inject_double_expiry(dataset)
        self._inject_gross_spend_tier_calculation(dataset)

        return dataset, self.anomalies

    def _next_anomaly_id(self) -> str:
        self._anomaly_counter += 1
        return f"ANOM-2026-{self._anomaly_counter:05d}"

    def _inject_balance_mismatch(self, dataset: Dict[str, Any]):
        """
        Category 1: Balance Mismatch (BR-01 Double-Entry Bookkeeping Violation)
        Tamper with an account balance directly without creating a ledger transaction.
        """
        accounts = dataset["loyalty_accounts"]
        eligible_accounts = [a for a in accounts if a.current_balance > 200]
        if not eligible_accounts:
            return

        target_acc = self.rng.choice(eligible_accounts)
        expected_balance = target_acc.current_balance
        variance = self.rng.choice([150, 250, 500, -100])
        tampered_balance = expected_balance + variance
        target_acc.current_balance = tampered_balance

        anomaly = InjectedAnomaly(
            anomaly_id=self._next_anomaly_id(),
            category="BALANCE_MISMATCH",
            affected_entities={"account_id": target_acc.account_id, "customer_id": target_acc.customer_id},
            expected_value=expected_balance,
            injected_value=tampered_balance,
            rule_violated="BR-01: Ledger Balance Invariant (Account balance must equal sum of journal transactions)",
            severity="CRITICAL",
            explanation=f"Direct database drift injected: account {target_acc.account_id} balance was modified by {variance} points without a matching journal transaction.",
        )
        self.anomalies.append(anomaly)

    def _inject_over_redemption(self, dataset: Dict[str, Any]):
        """
        Category 2: Over-Redemption (BR-08 Points Redemption Validation Violation)
        A redemption occurs where points_redeemed exceeds the account's available balance.
        """
        accounts = dataset["loyalty_accounts"]
        eligible = [a for a in accounts if 0 < a.current_balance < 300]
        if not eligible:
            eligible = accounts[:5]

        target_acc = self.rng.choice(eligible)
        available_balance = target_acc.current_balance
        excess_points = available_balance + 1000

        # Inject anomalous redemption
        rdm_id = f"RDM-ANOM-{self._anomaly_counter + 1:04d}"
        tx_id = f"PTS-ANOM-{self._anomaly_counter + 1:04d}"

        anom_rdm = SyntheticRedemption(
            redemption_id=rdm_id,
            account_id=target_acc.account_id,
            reward_id="REW-VOUCH-10",
            transaction_id=tx_id,
            points_redeemed=excess_points,
            voucher_code=f"VOUCH-ANOM-{self.rng.randint(100000, 999999)}",
            status="ISSUED",
            created_at=target_acc.updated_at,
            expires_at=None,
        )
        dataset["redemptions"].append(anom_rdm)

        anom_tx = SyntheticPointsTransaction(
            transaction_id=tx_id,
            account_id=target_acc.account_id,
            order_id=None,
            related_transaction_id=None,
            rule_id=None,
            entry_type="REDEMPTION",
            points=-excess_points,
            running_balance=available_balance - excess_points,
            idempotency_key=f"IDEM-ANOM-RDM-{rdm_id}",
            notes="Unauthorized over-redemption anomaly",
            created_at=target_acc.updated_at,
        )
        dataset["points_transactions"].append(anom_tx)
        target_acc.current_balance -= excess_points

        anomaly = InjectedAnomaly(
            anomaly_id=self._next_anomaly_id(),
            category="OVER_REDEMPTION",
            affected_entities={"account_id": target_acc.account_id, "redemption_id": rdm_id, "transaction_id": tx_id},
            expected_value=f"Points requested <= {available_balance}",
            injected_value=excess_points,
            rule_violated="BR-08: Points Redemption Validation (Redemption cannot exceed available positive balance)",
            severity="CRITICAL",
            explanation=f"Over-redemption allowed {excess_points} points on account {target_acc.account_id} which only had {available_balance} available.",
        )
        self.anomalies.append(anomaly)

    def _inject_unreversed_return(self, dataset: Dict[str, Any]):
        """
        Category 3: Un-Reversed Return (BR-10 Points Reversal on Return Violation)
        An order return refund was processed, but points were not reversed.
        """
        orders = [o for o in dataset["orders"] if Decimal(o.eligible_net_spend) > Decimal("50.00")]
        if not orders:
            return

        target_order = self.rng.choice(orders)
        refund_amount = Decimal(target_order.eligible_net_spend)
        expected_reversed_pts = int(refund_amount * Decimal("1.00"))

        ret_id = f"RET-ANOM-{self._anomaly_counter + 1:04d}"
        unreversed_return = SyntheticOrderReturn(
            return_id=ret_id,
            order_id=target_order.order_id,
            return_type="FULL",
            total_refund_amount=str(refund_amount),
            points_reversed=0,  # ANOMALY: 0 points reversed despite full refund!
            status="PROCESSED",
            created_at=target_order.order_date,
            lines=[],
        )
        dataset["order_returns"].append(unreversed_return)

        anomaly = InjectedAnomaly(
            anomaly_id=self._next_anomaly_id(),
            category="UNREVERSED_RETURN",
            affected_entities={"order_id": target_order.order_id, "return_id": ret_id, "customer_id": target_order.customer_id},
            expected_value=f"Reversal of {expected_reversed_pts} points",
            injected_value=0,
            rule_violated="BR-10: Points Reversal on Return (Returned merchandise points must be reversed)",
            severity="HIGH",
            explanation=f"Return {ret_id} for order {target_order.order_id} refunded ${refund_amount} but reversed 0 points.",
        )
        self.anomalies.append(anomaly)

    def _inject_double_expiry(self, dataset: Dict[str, Any]):
        """
        Category 4: Double Expiry (BR-11 Points Expiry Idempotency Violation)
        A points lot is expired twice, deducting points a second time.
        """
        lots = [l for l in dataset["points_lots"] if l.status == "EXPIRED"]
        if not lots:
            # Pick any lot and mark expired
            lots = dataset["points_lots"][:3]

        target_lot = self.rng.choice(lots)
        double_deduct_pts = target_lot.initial_points

        batch_id = f"EXP-ANOM-{self._anomaly_counter + 1:04d}"
        exp_item_id = f"EITEM-ANOM-{self._anomaly_counter + 1:04d}"
        exp_tx_id = f"PTS-ANOM-EXP-{self._anomaly_counter + 1:04d}"

        anom_item = SyntheticExpiryBatchItem(
            item_id=exp_item_id,
            batch_id=batch_id,
            lot_id=target_lot.lot_id,
            transaction_id=exp_tx_id,
            points_expired=double_deduct_pts,
            created_at=target_lot.expires_at,
        )
        dataset["expiry_batch_items"].append(anom_item)

        acc = next((a for a in dataset["loyalty_accounts"] if a.account_id == target_lot.account_id), None)
        if acc:
            acc.current_balance -= double_deduct_pts
            running_bal = acc.current_balance
        else:
            running_bal = -double_deduct_pts

        anom_tx = SyntheticPointsTransaction(
            transaction_id=exp_tx_id,
            account_id=target_lot.account_id,
            order_id=None,
            related_transaction_id=None,
            rule_id=None,
            entry_type="EXPIRY",
            points=-double_deduct_pts,
            running_balance=running_bal,
            idempotency_key=f"IDEM-EXP-DUP-{target_lot.lot_id}",
            notes=f"Duplicate expiry of lot {target_lot.lot_id}",
            created_at=target_lot.expires_at,
        )
        dataset["points_transactions"].append(anom_tx)

        anomaly = InjectedAnomaly(
            anomaly_id=self._next_anomaly_id(),
            category="DOUBLE_EXPIRY",
            affected_entities={"lot_id": target_lot.lot_id, "account_id": target_lot.account_id, "batch_id": batch_id},
            expected_value="Lot already expired; 0 points deducted",
            injected_value=f"Second deduction of {double_deduct_pts} points",
            rule_violated="BR-11: Points Expiry Idempotency (Expired lots cannot be processed a second time)",
            severity="HIGH",
            explanation=f"Lot {target_lot.lot_id} was expired a second time in batch {batch_id}, deducting {double_deduct_pts} extra points.",
        )
        self.anomalies.append(anomaly)

    def _inject_gross_spend_tier_calculation(self, dataset: Dict[str, Any]):
        """
        Category 5: Incorrect Tier Calculation using Gross Spend (BR-05 Violation)
        Upgrading customer to higher tier based on gross order amount (tax + shipping)
        when qualifying net spend was below threshold.
        """
        accounts = [a for a in dataset["loyalty_accounts"] if a.tier_id == "TIER-BRONZE"]
        if not accounts:
            accounts = dataset["loyalty_accounts"][:3]

        target_acc = self.rng.choice(accounts)
        original_qual_spend = Decimal(target_acc.qualifying_spend)

        # Elevate to Gold prematurely
        target_acc.tier_id = "TIER-GOLD"

        anomaly = InjectedAnomaly(
            anomaly_id=self._next_anomaly_id(),
            category="GROSS_SPEND_TIER_CALCULATION",
            affected_entities={"account_id": target_acc.account_id, "customer_id": target_acc.customer_id},
            expected_value="TIER-BRONZE (Qualifying spend < $500.00)",
            injected_value="TIER-GOLD (Calculated using gross revenue including tax/shipping)",
            rule_violated="BR-05: Qualifying Spend vs Gross Spend (Tier upgrades must evaluate net merchandise spend only)",
            severity="MEDIUM",
            explanation=f"Customer {target_acc.customer_id} upgraded to TIER-GOLD with qualifying spend of only ${original_qual_spend} due to tax/shipping gross inflation.",
        )
        self.anomalies.append(anomaly)
