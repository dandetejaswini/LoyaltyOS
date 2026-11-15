"""
LoyaltyOS — Deterministic Synthetic Data Generator
Generates realistic, fully auditable loyalty data adhering to Phase 0 rules.
"""

import math
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional

from backend.app.seed.config import (
    DEFAULT_SEED,
    GeneratorScale,
    TEST_SCALE,
    FULL_SCALE,
    TIERS_CONFIG,
    PRODUCT_CATALOG,
    REWARDS_CATALOG,
)
from backend.app.seed.models import (
    SyntheticCustomer,
    SyntheticLoyaltyAccount,
    SyntheticOrder,
    SyntheticOrderLine,
    SyntheticPointsTransaction,
    SyntheticPointsLot,
    SyntheticRedemption,
    SyntheticLotAllocation,
    SyntheticOrderReturn,
    SyntheticOrderReturnLine,
    SyntheticExpiryBatch,
    SyntheticExpiryBatchItem,
)


FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]


class SyntheticDataGenerator:
    """
    Deterministic Synthetic Data Generator for LoyaltyOS.
    Produces valid baseline data that mathematically reconciles across all entities.
    """

    def __init__(self, seed: int = DEFAULT_SEED, scale: GeneratorScale = TEST_SCALE):
        self.seed = seed
        self.scale = scale
        self.rng = random.Random(seed)

        # Baseline storage containers
        self.customers: List[SyntheticCustomer] = []
        self.accounts: Dict[str, SyntheticLoyaltyAccount] = {}  # customer_id -> account
        self.orders: List[SyntheticOrder] = []
        self.order_lines: List[SyntheticOrderLine] = []
        self.transactions: List[SyntheticPointsTransaction] = []
        self.lots: List[SyntheticPointsLot] = []
        self.account_lots: Dict[str, List[SyntheticPointsLot]] = {}  # account_id -> list of lots
        self.redemptions: List[SyntheticRedemption] = []
        self.allocations: List[SyntheticLotAllocation] = []
        self.returns: List[SyntheticOrderReturn] = []
        self.return_lines: List[SyntheticOrderReturnLine] = []
        self.expiry_batches: List[SyntheticExpiryBatch] = []
        self.expiry_batch_items: List[SyntheticExpiryBatchItem] = []

        # Sequence counters
        self._tx_counter = 0
        self._lot_counter = 0
        self._rdm_counter = 0
        self._ret_counter = 0
        self._alloc_counter = 0
        self._exp_batch_counter = 0
        self._exp_item_counter = 0

    def generate_all(self) -> Dict[str, Any]:
        """Generates all baseline entities in valid relational order."""
        self._generate_customers_and_accounts()
        self._generate_orders_and_ledger()
        return self.get_dataset()

    def _generate_customers_and_accounts(self):
        """Generates customers and initializes their loyalty accounts."""
        start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        for i in range(1, self.scale.num_customers + 1):
            customer_id = f"CUST-{i:06d}"
            fn = self.rng.choice(FIRST_NAMES)
            ln = self.rng.choice(LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}.{i}@example.com"
            phone = f"+1{self.rng.randint(200, 999)}{self.rng.randint(1000000, 9999999)}"
            status = "ACTIVE" if self.rng.random() > 0.02 else "SUSPENDED"

            # Spread registration dates across 18 months
            days_offset = self.rng.randint(0, 540)
            reg_date = start_date + timedelta(days=days_offset, minutes=self.rng.randint(0, 1439))
            reg_str = reg_date.isoformat()

            cust = SyntheticCustomer(
                customer_id=customer_id,
                email=email,
                first_name=fn,
                last_name=ln,
                phone=phone,
                status=status,
                created_at=reg_str,
                updated_at=reg_str,
            )
            self.customers.append(cust)

            # Loyalty Account initialized to Bronze
            account_id = f"LOY-{customer_id}"
            acc = SyntheticLoyaltyAccount(
                account_id=account_id,
                customer_id=customer_id,
                tier_id="TIER-BRONZE",
                current_balance=0,
                lifetime_accrued=0,
                lifetime_redeemed=0,
                qualifying_spend="0.00",
                status="ACTIVE",
                created_at=reg_str,
                updated_at=reg_str,
            )
            self.accounts[customer_id] = acc
            self.account_lots[account_id] = []

    def _determine_tier(self, qualifying_spend: Decimal) -> Dict[str, Any]:
        """Calculates current tier based on qualifying spend (BR-05)."""
        current_tier = TIERS_CONFIG[0]
        for t in TIERS_CONFIG:
            if qualifying_spend >= t["min_spend"]:
                current_tier = t
        return current_tier

    def _generate_orders_and_ledger(self):
        """
        Generates orders, accrual transactions, FIFO lots, redemptions,
        returns/reversals, and lot expirations.
        """
        cust_ids = [c.customer_id for c in self.customers]

        # Weights: Pareto-style distribution (20% of customers place 60% of orders)
        weights = [
            5.0 if i < (len(cust_ids) * 0.2) else 1.0
            for i in range(len(cust_ids))
        ]

        base_date = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        current_sim_date = datetime(2026, 11, 15, 0, 0, 0, tzinfo=timezone.utc)

        line_counter = 0

        for order_idx in range(1, self.scale.num_orders + 1):
            customer_id = self.rng.choices(cust_ids, weights=weights, k=1)[0]
            account = self.accounts[customer_id]

            # Order date between customer registration and sim date
            cust_reg = datetime.fromisoformat(account.created_at)
            max_days = max(1, (current_sim_date - cust_reg).days)
            order_days = self.rng.randint(0, max_days)
            order_dt = cust_reg + timedelta(days=order_days, seconds=self.rng.randint(0, 86399))
            order_date_str = order_dt.isoformat()

            order_id = f"ORD-2026-{order_idx:06d}"

            # 1. Generate Order Lines
            num_lines = self.rng.randint(1, 4)
            order_lines_list: List[SyntheticOrderLine] = []
            order_eligible_spend = Decimal("0.00")
            order_subtotal = Decimal("0.00")

            for line_no in range(1, num_lines + 1):
                line_counter += 1
                prod = self.rng.choice(PRODUCT_CATALOG)
                qty = self.rng.randint(1, 3)
                unit_price = prod["price"]
                item_discount = Decimal("0.00")
                if self.rng.random() < 0.15:
                    item_discount = (unit_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                net_line = (unit_price * Decimal(qty)) - item_discount
                order_subtotal += net_line
                if prod["is_eligible"]:
                    order_eligible_spend += net_line

                line_obj = SyntheticOrderLine(
                    order_line_id=f"LINE-2026-{line_counter:08d}",
                    order_id=order_id,
                    line_number=line_no,
                    sku=prod["sku"],
                    product_name=prod["name"],
                    category=prod["category"],
                    quantity=qty,
                    unit_price=str(unit_price),
                    item_discount=str(item_discount),
                    net_amount=str(net_line),
                    is_eligible=prod["is_eligible"],
                    created_at=order_date_str,
                )
                order_lines_list.append(line_obj)
                self.order_lines.append(line_obj)

            tax_amount = (order_subtotal * Decimal("0.08")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            shipping_amount = Decimal("0.00") if order_subtotal > Decimal("100.00") else Decimal("9.99")
            discount_amount = Decimal("0.00")
            gross_amount = order_subtotal + tax_amount + shipping_amount

            order_obj = SyntheticOrder(
                order_id=order_id,
                customer_id=customer_id,
                order_date=order_date_str,
                gross_amount=str(gross_amount),
                tax_amount=str(tax_amount),
                shipping_amount=str(shipping_amount),
                discount_amount=str(discount_amount),
                eligible_net_spend=str(order_eligible_spend),
                status="COMPLETED",
                accrual_status="ACCRUED",
                created_at=order_date_str,
                lines=order_lines_list,
            )
            self.orders.append(order_obj)

            # 2. Accrual Calculation (BR-02, BR-04, BR-05)
            # Evaluate tier based on existing qualifying spend
            curr_qual_spend = Decimal(account.qualifying_spend)
            tier_info = self._determine_tier(curr_qual_spend)
            tier_mult = tier_info["multiplier"]

            # Points awarded = floor(eligible_net_spend * multiplier)
            pts_earned = math.floor(float(order_eligible_spend * tier_mult))

            if pts_earned > 0:
                self._tx_counter += 1
                self._lot_counter += 1

                account.current_balance += pts_earned
                account.lifetime_accrued += pts_earned
                new_qual_spend = curr_qual_spend + order_eligible_spend
                account.qualifying_spend = str(new_qual_spend)

                # Check for tier upgrade
                new_tier = self._determine_tier(new_qual_spend)
                account.tier_id = new_tier["tier_id"]

                tx_id = f"PTS-2026-{self._tx_counter:08d}"
                accrual_tx = SyntheticPointsTransaction(
                    transaction_id=tx_id,
                    account_id=account.account_id,
                    order_id=order_id,
                    related_transaction_id=None,
                    rule_id=None,
                    entry_type="ACCRUAL",
                    points=pts_earned,
                    running_balance=account.current_balance,
                    idempotency_key=f"IDEM-ACC-ORD-{order_id}",
                    notes=f"Order {order_id} points accrual at {tier_mult}x multiplier",
                    created_at=order_date_str,
                )
                self.transactions.append(accrual_tx)

                # Points Lot (365-day expiration policy)
                lot_id = f"LOT-2026-{self._lot_counter:08d}"
                expires_at = (order_dt + timedelta(days=365)).isoformat()
                lot = SyntheticPointsLot(
                    lot_id=lot_id,
                    transaction_id=tx_id,
                    account_id=account.account_id,
                    initial_points=pts_earned,
                    remaining_points=pts_earned,
                    status="ACTIVE",
                    expires_at=expires_at,
                    created_at=order_date_str,
                    updated_at=order_date_str,
                )
                self.lots.append(lot)
                self.account_lots[account.account_id].append(lot)

            # 3. Simulate Redemptions (FIFO Lot Allocation)
            if self.rng.random() < self.scale.redemption_ratio:
                affordable_rewards = [
                    r for r in REWARDS_CATALOG
                    if r["points_required"] <= account.current_balance
                ]
                if affordable_rewards:
                    reward = self.rng.choice(affordable_rewards)
                    pts_needed = reward["points_required"]

                    # FIFO lot allocation by expires_at ASC, created_at ASC
                    active_lots = [
                        l for l in self.account_lots[account.account_id]
                        if l.remaining_points > 0 and l.status in ("ACTIVE", "PARTIALLY_REDEEMED")
                    ]
                    active_lots.sort(key=lambda x: (x.expires_at, x.created_at))

                    pts_allocated = 0
                    alloc_records = []

                    self._rdm_counter += 1
                    self._tx_counter += 1

                    rdm_id = f"RDM-2026-{self._rdm_counter:06d}"
                    rdm_tx_id = f"PTS-2026-{self._tx_counter:08d}"
                    rdm_date = (order_dt + timedelta(hours=self.rng.randint(1, 48))).isoformat()

                    account.current_balance -= pts_needed
                    account.lifetime_redeemed += pts_needed

                    for lot in active_lots:
                        if pts_allocated >= pts_needed:
                            break
                        take = min(lot.remaining_points, pts_needed - pts_allocated)
                        lot.remaining_points -= take
                        pts_allocated += take
                        lot.status = "EXHAUSTED" if lot.remaining_points == 0 else "PARTIALLY_REDEEMED"
                        lot.updated_at = rdm_date

                        self._alloc_counter += 1
                        alloc = SyntheticLotAllocation(
                            allocation_id=f"ALC-2026-{self._alloc_counter:08d}",
                            lot_id=lot.lot_id,
                            redemption_id=rdm_id,
                            transaction_id=rdm_tx_id,
                            points_allocated=take,
                            created_at=rdm_date,
                        )
                        self.allocations.append(alloc)

                    rdm_tx = SyntheticPointsTransaction(
                        transaction_id=rdm_tx_id,
                        account_id=account.account_id,
                        order_id=None,
                        related_transaction_id=None,
                        rule_id=None,
                        entry_type="REDEMPTION",
                        points=-pts_needed,
                        running_balance=account.current_balance,
                        idempotency_key=f"IDEM-RDM-{rdm_id}",
                        notes=f"Redeemed {reward['name']} for {pts_needed} points",
                        created_at=rdm_date,
                    )
                    self.transactions.append(rdm_tx)

                    rdm_obj = SyntheticRedemption(
                        redemption_id=rdm_id,
                        account_id=account.account_id,
                        reward_id=reward["reward_id"],
                        transaction_id=rdm_tx_id,
                        points_redeemed=pts_needed,
                        voucher_code=f"VOUCH-{self.rng.randint(100000, 999999)}-{self._rdm_counter:04d}",
                        status="ISSUED",
                        created_at=rdm_date,
                        expires_at=(datetime.fromisoformat(rdm_date) + timedelta(days=90)).isoformat(),
                    )
                    self.redemptions.append(rdm_obj)

            # 4. Simulate Returns & Reversals (Subset of orders)
            if self.rng.random() < self.scale.return_ratio and order_lines_list:
                return_line = self.rng.choice(order_lines_list)
                if return_line.is_eligible and Decimal(return_line.net_amount) > 0:
                    ret_date = (order_dt + timedelta(days=self.rng.randint(2, 14))).isoformat()
                    refund_amount = Decimal(return_line.net_amount)
                    pts_to_reverse = math.floor(float(refund_amount * tier_mult))

                    if pts_to_reverse > 0:
                        self._ret_counter += 1
                        self._tx_counter += 1

                        ret_id = f"RET-2026-{self._ret_counter:06d}"
                        ret_tx_id = f"PTS-2026-{self._tx_counter:08d}"

                        account.current_balance -= pts_to_reverse
                        account.qualifying_spend = str(max(Decimal("0.00"), Decimal(account.qualifying_spend) - refund_amount))

                        ret_line_obj = SyntheticOrderReturnLine(
                            return_line_id=f"RLINE-2026-{self._ret_counter:06d}-1",
                            return_id=ret_id,
                            order_line_id=return_line.order_line_id,
                            quantity_returned=return_line.quantity,
                            refund_amount=str(refund_amount),
                            created_at=ret_date,
                        )
                        self.return_lines.append(ret_line_obj)

                        ret_obj = SyntheticOrderReturn(
                            return_id=ret_id,
                            order_id=order_id,
                            return_type="PARTIAL",
                            total_refund_amount=str(refund_amount),
                            points_reversed=pts_to_reverse,
                            status="PROCESSED",
                            created_at=ret_date,
                            lines=[ret_line_obj],
                        )
                        self.returns.append(ret_obj)

                        ret_tx = SyntheticPointsTransaction(
                            transaction_id=ret_tx_id,
                            account_id=account.account_id,
                            order_id=order_id,
                            related_transaction_id=None,
                            rule_id=None,
                            entry_type="REVERSAL",
                            points=-pts_to_reverse,
                            running_balance=account.current_balance,
                            idempotency_key=f"IDEM-RET-{ret_id}",
                            notes=f"Reversal of {pts_to_reverse} points for return {ret_id}",
                            created_at=ret_date,
                        )
                        self.transactions.append(ret_tx)

        # 5. Simulate Points Expiries for Expired Lots
        self._simulate_expiries(current_sim_date)

    def _simulate_expiries(self, sim_date: datetime):
        """Simulates end-of-year lot expiration on eligible lots past 365 days."""
        expired_lots_by_acc: Dict[str, List[SyntheticPointsLot]] = {}

        for lot in self.lots:
            lot_exp = datetime.fromisoformat(lot.expires_at)
            if lot_exp <= sim_date and lot.remaining_points > 0 and lot.status in ("ACTIVE", "PARTIALLY_REDEEMED"):
                expired_lots_by_acc.setdefault(lot.account_id, []).append(lot)

        if not expired_lots_by_acc:
            return

        self._exp_batch_counter += 1
        batch_id = f"EXP-2026-{self._exp_batch_counter:04d}"
        batch_items = []
        total_pts_expired = 0

        batch_date = sim_date.isoformat()

        for acc_id, lots in expired_lots_by_acc.items():
            acc = next(a for a in self.accounts.values() if a.account_id == acc_id)
            for lot in lots:
                pts_expired = lot.remaining_points
                lot.remaining_points = 0
                lot.status = "EXPIRED"
                lot.updated_at = batch_date

                self._exp_item_counter += 1
                self._tx_counter += 1

                exp_tx_id = f"PTS-2026-{self._tx_counter:08d}"
                acc.current_balance -= pts_expired

                item = SyntheticExpiryBatchItem(
                    item_id=f"EITEM-2026-{self._exp_item_counter:08d}",
                    batch_id=batch_id,
                    lot_id=lot.lot_id,
                    transaction_id=exp_tx_id,
                    points_expired=pts_expired,
                    created_at=batch_date,
                )
                batch_items.append(item)
                self.expiry_batch_items.append(item)
                total_pts_expired += pts_expired

                exp_tx = SyntheticPointsTransaction(
                    transaction_id=exp_tx_id,
                    account_id=acc.account_id,
                    order_id=None,
                    related_transaction_id=None,
                    rule_id=None,
                    entry_type="EXPIRY",
                    points=-pts_expired,
                    running_balance=acc.current_balance,
                    idempotency_key=f"IDEM-EXP-{lot.lot_id}",
                    notes=f"Lot {lot.lot_id} points expired",
                    created_at=batch_date,
                )
                self.transactions.append(exp_tx)

        batch = SyntheticExpiryBatch(
            batch_id=batch_id,
            cutoff_date=batch_date,
            total_lots_processed=len(batch_items),
            total_points_expired=total_pts_expired,
            status="COMPLETED",
            created_at=batch_date,
            items=batch_items,
        )
        self.expiry_batches.append(batch)

    def get_dataset(self) -> Dict[str, Any]:
        """Returns the complete structured dataset."""
        return {
            "seed": self.seed,
            "scale": self.scale.name,
            "customers": self.customers,
            "loyalty_accounts": list(self.accounts.values()),
            "orders": self.orders,
            "order_lines": self.order_lines,
            "points_transactions": self.transactions,
            "points_lots": self.lots,
            "redemptions": self.redemptions,
            "points_lot_allocations": self.allocations,
            "order_returns": self.returns,
            "order_return_lines": self.return_lines,
            "expiry_batches": self.expiry_batches,
            "expiry_batch_items": self.expiry_batch_items,
        }
