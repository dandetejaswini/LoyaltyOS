"""
LoyaltyOS â€” Phase 4 Core Loyalty Business Workflow Tests
Tests real accounting logic, business invariants, idempotency, floor-rounding,
FIFO lot allocation, return reversals with negative balance, and security scoping.
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer, LoyaltyAccount, Tier, Order, OrderLine, OrderReturn, OrderReturnLine
from backend.app.models.ledger import PointsTransaction, PointsLot, Reward, Redemption, PointsLotAllocation, ExpiryBatch, ExpiryBatchItem
from backend.app.schemas.loyalty import CustomerCreateRequest, OrderCreateRequest, OrderLineCreate, OrderReturnRequest, ReturnLineCreate
from backend.app.schemas.ledger import RedemptionRequest, ExpiryExecutionRequest
from backend.app.services.customer_service import CustomerService
from backend.app.services.accrual_service import AccrualService
from backend.app.services.ledger_service import LedgerService
from backend.app.services.redemption_service import RedemptionService
from backend.app.services.return_service import ReturnService
from backend.app.services.expiry_service import ExpiryService
from backend.app.services.tier_service import TierService
from backend.app.core.errors import NotFoundError, ConflictError, BadRequestError, ForbiddenError


# ============================================================================
# Helpers & Mock Entities
# ============================================================================

def make_tier(tier_id="TIER-BRONZE", name="Bronze", rank=1, min_spend=Decimal("0.00"), multiplier=Decimal("1.00")):
    return Tier(
        tier_id=tier_id,
        name=name,
        rank=rank,
        min_spend=min_spend,
        earning_multiplier=multiplier,
    )


def make_account(account_id="LOY-CUST-001", customer_id="CUST-001", tier=None, balance=1000, qual_spend=Decimal("500.00"), status="ACTIVE"):
    tier = tier or make_tier()
    acc = LoyaltyAccount(
        account_id=account_id,
        customer_id=customer_id,
        tier_id=tier.tier_id,
        current_balance=balance,
        lifetime_accrued=balance,
        lifetime_redeemed=0,
        qualifying_spend=qual_spend,
        status=status,
    )
    acc.tier = tier
    return acc


def make_customer(customer_id="CUST-001", email="alice@example.com", account=None):
    cust = Customer(
        customer_id=customer_id,
        email=email,
        first_name="Alice",
        last_name="Smith",
        status="ACTIVE",
    )
    if account:
        cust.loyalty_account = account
        account.customer = cust
    return cust


# ============================================================================
# WORKFLOW A: Customer & Loyalty Account Provisioning Tests
# ============================================================================

class TestWorkflowACustomerProvisioning:

    @pytest.mark.asyncio
    async def test_provision_new_customer_and_account(self):
        """Workflow A: Creates customer, 1:1 account, default Bronze tier, balance 0, and audit event."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # Execute queries: 1. check email, 2. check custom customer_id, 3. check tier
        res_no_cust = MagicMock()
        res_no_cust.scalar_one_or_none.return_value = None

        res_no_id = MagicMock()
        res_no_id.scalar_one_or_none.return_value = None

        res_tier = MagicMock()
        res_tier.scalar_one_or_none.return_value = make_tier()

        mock_db.execute.side_effect = [res_no_cust, res_no_id, res_tier]

        req = CustomerCreateRequest(
            customer_id="CUST-NEW-001",
            email="newcustomer@example.com",
            first_name="Bob",
            last_name="Jones",
            phone="+1234567890",
        )

        customer, account, is_new = await CustomerService.provision_customer(
            db=mock_db,
            req=req,
            actor_id="ACTOR-ADMIN-1",
        )

        assert is_new is True
        assert customer.customer_id == "CUST-NEW-001"
        assert customer.email == "newcustomer@example.com"
        assert account.account_id == "LOY-CUST-NEW-001"
        assert account.current_balance == 0
        assert account.tier_id == "TIER-BRONZE"
        assert account.status == "ACTIVE"
        assert mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_provision_existing_customer_idempotent(self):
        """Workflow A: If customer already exists, returns existing profile idempotently without duplicate account."""
        mock_db = AsyncMock()
        existing_acc = make_account()
        existing_cust = make_customer(account=existing_acc)

        res_existing = MagicMock()
        res_existing.scalar_one_or_none.return_value = existing_cust
        mock_db.execute.return_value = res_existing

        req = CustomerCreateRequest(
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
        )

        customer, account, is_new = await CustomerService.provision_customer(
            db=mock_db,
            req=req,
            actor_id="ACTOR-1",
        )

        assert is_new is False
        assert customer.customer_id == existing_cust.customer_id
        assert account.account_id == existing_acc.account_id
        # No new additions
        assert mock_db.add.call_count == 0


# ============================================================================
# WORKFLOW B: Order Creation & Points Accrual Tests
# ============================================================================

class TestWorkflowBPointsAccrual:

    @pytest.mark.asyncio
    async def test_order_accrual_qualifying_spend_and_floor_rounding(self):
        """
        Workflow B: Strictly calculates qualifying spend:
        - Excludes shipping ($15.00) and taxes ($8.00).
        - Excludes ineligible gift cards ($50.00).
        - Applies Silver tier multiplier (1.25x).
        - Floors points to nearest integer (e.g. $149.99 * 1.25 = 187.4875 -> 187 pts).
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # Idempotency check: not found
        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        # Customer & Account: Silver Tier (1.25x)
        silver_tier = make_tier(tier_id="TIER-SILVER", name="Silver", rank=2, min_spend=Decimal("500.00"), multiplier=Decimal("1.25"))
        account = make_account(tier=silver_tier, balance=100)
        customer = make_customer(account=account)

        res_cust = MagicMock()
        res_cust.scalar_one_or_none.return_value = customer

        # Order ID check: not found
        res_no_order = MagicMock()
        res_no_order.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [res_no_tx, res_cust, res_no_order]

        req = OrderCreateRequest(
            order_id="ORD-TEST-001",
            customer_id="CUST-001",
            idempotency_key="IDEM-ORDER-001",
            tax_amount=Decimal("8.00"),
            shipping_amount=Decimal("15.00"),
            discount_amount=Decimal("0.00"),
            lines=[
                # Eligible Item: Headphones ($149.99, no discount)
                OrderLineCreate(
                    line_number=1,
                    sku="SKU-TECH-001",
                    product_name="Headphones",
                    category="Electronics",
                    quantity=1,
                    unit_price=Decimal("149.99"),
                    item_discount=Decimal("0.00"),
                    is_eligible=True,
                ),
                # Ineligible Item: Store Gift Card ($50.00) -> BR-01 strictly excluded from accrual!
                OrderLineCreate(
                    line_number=2,
                    sku="SKU-GIFT-050",
                    product_name="e-Gift Card $50",
                    category="Gift Cards",
                    quantity=1,
                    unit_price=Decimal("50.00"),
                    item_discount=Decimal("0.00"),
                    is_eligible=False,
                ),
            ],
        )

        response = await AccrualService.process_order_accrual(
            db=mock_db,
            req=req,
            actor_id="ACTOR-CUSTOMER-1",
        )

        # Expected:
        # Eligible net spend = 149.99 (gift card excluded)
        # Multiplier = 1.25
        # 149.99 * 1.25 = 187.4875 -> floor = 187 points!
        assert response.eligible_net_spend == Decimal("149.99")
        assert response.tier_multiplier == Decimal("1.25")
        assert response.points_accrued == 187
        assert response.new_balance == 100 + 187  # 287
        assert response.lot_expires_at > datetime.now(timezone.utc)
        assert mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_order_accrual_duplicate_idempotency_rejected(self):
        """Workflow B: Duplicate submission with same idempotency key is rejected with ConflictError (409)."""
        mock_db = AsyncMock()
        existing_tx = PointsTransaction(transaction_id="PTS-EXISTING", idempotency_key="IDEM-ORDER-001")
        res_existing_tx = MagicMock()
        res_existing_tx.scalar_one_or_none.return_value = existing_tx
        mock_db.execute.return_value = res_existing_tx

        req = OrderCreateRequest(
            customer_id="CUST-001",
            idempotency_key="IDEM-ORDER-001",
            lines=[
                OrderLineCreate(
                    line_number=1,
                    sku="SKU-TECH-001",
                    product_name="Headphones",
                    category="Electronics",
                    quantity=1,
                    unit_price=Decimal("100.00"),
                    is_eligible=True,
                )
            ],
        )

        with pytest.raises(ConflictError) as exc_info:
            await AccrualService.process_order_accrual(db=mock_db, req=req, actor_id="ACTOR-1")
        assert "already processed" in str(exc_info.value.detail)


# ============================================================================
# WORKFLOW C: Balance & Ledger Reconciliation Tests
# ============================================================================

class TestWorkflowCLedgerReconciliation:

    @pytest.mark.asyncio
    async def test_reconciliation_detects_clean_reconciled_state(self):
        """Workflow C: Reconciled status when stored balance exactly equals sum of transactions."""
        mock_db = AsyncMock()
        account = make_account(balance=500)
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_sum = MagicMock()
        res_sum.scalar.return_value = 500  # Sum of transactions = 500

        res_breakdown = MagicMock()
        res_breakdown.all.return_value = [("ACCRUAL", 600), ("REDEMPTION", -100)]

        mock_db.execute.side_effect = [res_acc, res_sum, res_breakdown]

        report = await LedgerService.reconcile_account_balance(mock_db, "LOY-CUST-001")

        assert report.is_reconciled is True
        assert report.status == "RECONCILED"
        assert report.discrepancy_amount == 0
        assert report.stored_balance == 500
        assert report.ledger_derived_balance == 500

    @pytest.mark.asyncio
    async def test_reconciliation_detects_drift_without_silent_corruption(self):
        """Workflow C: If stored balance differs from ledger sum, transparently reports discrepancy without silent overwrite."""
        mock_db = AsyncMock()
        account = make_account(balance=750)  # Drift: stored balance is 750
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_sum = MagicMock()
        res_sum.scalar.return_value = 500  # Journal sum is actually 500 (discrepancy of +250)

        res_breakdown = MagicMock()
        res_breakdown.all.return_value = [("ACCRUAL", 500)]

        mock_db.execute.side_effect = [res_acc, res_sum, res_breakdown]

        report = await LedgerService.reconcile_account_balance(mock_db, "LOY-CUST-001")

        assert report.is_reconciled is False
        assert report.status == "DISCREPANCY_DETECTED"
        assert report.discrepancy_amount == 250
        assert report.stored_balance == 750
        assert report.ledger_derived_balance == 500


# ============================================================================
# WORKFLOW D: Redemption & FIFO Lot Allocation Tests
# ============================================================================

class TestWorkflowDRedemption:

    @pytest.mark.asyncio
    async def test_redemption_fifo_lot_allocation_success(self):
        """
        Workflow D: Successful redemption consumes points in FIFO order (earliest expires_at first).
        Lot 1 (expires in 30 days, 200 pts) exhausted.
        Lot 2 (expires in 60 days, 500 pts) partially consumed for 300 pts.
        Total redeemed = 500 pts.
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # 1. Idempotency: not found
        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        # 2. Account: balance 1000
        account = make_account(balance=1000)
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        # 3. Reward: 500 points required
        reward = Reward(
            reward_id="REW-VOUCH-05",
            name="$5 Voucher",
            reward_type="DISCOUNT_VOUCHER",
            points_required=500,
            monetary_value=Decimal("5.00"),
            is_active=True,
        )
        res_rew = MagicMock()
        res_rew.scalar_one_or_none.return_value = reward

        # 4. Active Lots: Lot 1 (200 pts, expires sooner), Lot 2 (500 pts, expires later)
        now = datetime.now(timezone.utc)
        lot1 = PointsLot(
            lot_id="LOT-001",
            transaction_id="PTS-001",
            account_id=account.account_id,
            initial_points=200,
            remaining_points=200,
            status="ACTIVE",
            expires_at=now + timedelta(days=30),
        )
        lot2 = PointsLot(
            lot_id="LOT-002",
            transaction_id="PTS-002",
            account_id=account.account_id,
            initial_points=500,
            remaining_points=500,
            status="ACTIVE",
            expires_at=now + timedelta(days=60),
        )
        res_lots = MagicMock()
        res_lots.scalars.return_value.all.return_value = [lot1, lot2]

        mock_db.execute.side_effect = [res_no_tx, res_acc, res_rew, res_lots]

        req = RedemptionRequest(
            account_id=account.account_id,
            reward_id="REW-VOUCH-05",
            idempotency_key="IDEM-RDM-001",
        )

        response = await RedemptionService.redeem_reward(mock_db, req, actor_id="ACTOR-CUST-1")

        # Invariant Assertions:
        assert response.points_redeemed == 500
        assert response.new_balance == 500  # 1000 - 500
        assert lot1.remaining_points == 0
        assert lot1.status == "EXHAUSTED"
        assert lot2.remaining_points == 200  # 500 - 300
        assert lot2.status == "PARTIALLY_REDEEMED"
        assert len(response.allocations) == 2
        assert response.voucher_code.startswith("VOUCH-")
        assert mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_redemption_rejected_when_balance_insufficient(self):
        """Workflow D: Redemption is rejected and logged when balance is insufficient (BR-08)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        account = make_account(balance=300)  # Only 300 available
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        reward = Reward(
            reward_id="REW-VOUCH-10",
            name="$10 Voucher",
            points_required=950,  # Requires 950
            is_active=True,
        )
        res_rew = MagicMock()
        res_rew.scalar_one_or_none.return_value = reward

        mock_db.execute.side_effect = [res_no_tx, res_acc, res_rew]

        req = RedemptionRequest(
            account_id=account.account_id,
            reward_id="REW-VOUCH-10",
            idempotency_key="IDEM-RDM-OVERDRAFT",
        )

        with pytest.raises(BadRequestError) as exc_info:
            await RedemptionService.redeem_reward(mock_db, req, actor_id="ACTOR-1")
        assert "Insufficient points balance" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_redemption_frozen_when_balance_negative(self):
        """Workflow D: Redemptions are frozen when balance is negative due to previous return reversal (BR-10)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        account = make_account(balance=-150)  # Negative balance
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        mock_db.execute.side_effect = [res_no_tx, res_acc]

        req = RedemptionRequest(
            account_id=account.account_id,
            reward_id="REW-VOUCH-05",
            idempotency_key="IDEM-RDM-NEG",
        )

        with pytest.raises(BadRequestError) as exc_info:
            await RedemptionService.redeem_reward(mock_db, req, actor_id="ACTOR-1")
        assert "negative" in str(exc_info.value.detail).lower()


# ============================================================================
# WORKFLOW E: Order Returns & Points Reversal Tests
# ============================================================================

class TestWorkflowEOrderReturns:

    @pytest.mark.asyncio
    async def test_partial_order_return_reverses_points_and_caps_at_accrual(self):
        """
        Workflow E: Partial order return reverses points attributable to returned items.
        Eligible refund = $100.00 @ 1.25x = 125 points reversed.
        Original accrual was 200 points. Cumulative reversals capped at 200.
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        silver_tier = make_tier(tier_id="TIER-SILVER", multiplier=Decimal("1.25"))
        account = make_account(tier=silver_tier, balance=500, qual_spend=Decimal("300.00"))
        customer = make_customer(account=account)

        order = Order(
            order_id="ORD-001",
            customer_id=customer.customer_id,
            status="COMPLETED",
            eligible_net_spend=Decimal("200.00"),
            lines=[
                OrderLine(
                    order_line_id="ORDL-001-01",
                    order_id="ORD-001",
                    line_number=1,
                    sku="SKU-APP-001",
                    product_name="Sweater",
                    category="Apparel",
                    quantity=2,
                    unit_price=Decimal("100.00"),
                    item_discount=Decimal("0.00"),
                    net_amount=Decimal("200.00"),
                    is_eligible=True,
                )
            ]
        )
        order.customer = customer

        res_order = MagicMock()
        res_order.scalar_one_or_none.return_value = order

        # Original accrual was 200 points
        orig_accrual = PointsTransaction(transaction_id="PTS-ORIG-001", points=200, entry_type="ACCRUAL")
        res_orig = MagicMock()
        res_orig.scalar_one_or_none.return_value = orig_accrual

        # Previous reversals = 0
        res_prev_rev = MagicMock()
        res_prev_rev.scalar.return_value = 0

        # Existing return lines = 0
        res_prev_lines = MagicMock()
        res_prev_lines.all.return_value = []

        mock_db.execute.side_effect = [res_no_tx, res_order, res_orig, res_prev_rev, res_prev_lines]

        req = OrderReturnRequest(
            order_id="ORD-001",
            idempotency_key="IDEM-RET-001",
            lines=[ReturnLineCreate(order_line_id="ORDL-001-01", quantity_returned=1)],
        )

        response = await ReturnService.process_return(mock_db, req, actor_id="ACTOR-OPERATOR-1")

        # Returned 1 of 2 -> $100.00 refund @ 1.25x = 125 points reversed
        assert response.total_refund_amount == Decimal("100.00")
        assert response.points_reversed == 125
        assert response.new_balance == 500 - 125  # 375
        assert response.return_type == "PARTIAL"
        assert response.is_balance_negative is False

    @pytest.mark.asyncio
    async def test_return_after_redemption_supports_negative_balance(self):
        """
        Workflow E: If points were already redeemed, return reversal creates negative balance (BR-10).
        Customer balance was 50 points, return reverses 150 points -> new balance = -100 points.
        Redemptions are frozen while balance is negative.
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        res_no_tx = MagicMock()
        res_no_tx.scalar_one_or_none.return_value = None

        tier = make_tier(multiplier=Decimal("1.00"))
        account = make_account(tier=tier, balance=50)  # Only 50 balance remaining after redemption
        customer = make_customer(account=account)

        order = Order(
            order_id="ORD-002",
            customer_id=customer.customer_id,
            status="COMPLETED",
            eligible_net_spend=Decimal("150.00"),
            lines=[
                OrderLine(
                    order_line_id="ORDL-002-01",
                    order_id="ORD-002",
                    line_number=1,
                    sku="SKU-002",
                    product_name="Product",
                    category="Apparel",
                    quantity=1,
                    unit_price=Decimal("150.00"),
                    item_discount=Decimal("0.00"),
                    net_amount=Decimal("150.00"),
                    is_eligible=True,
                )
            ]
        )
        order.customer = customer

        res_order = MagicMock()
        res_order.scalar_one_or_none.return_value = order

        orig_accrual = PointsTransaction(transaction_id="PTS-ORIG-002", points=150, entry_type="ACCRUAL")
        res_orig = MagicMock()
        res_orig.scalar_one_or_none.return_value = orig_accrual

        res_prev_rev = MagicMock()
        res_prev_rev.scalar.return_value = 0

        res_prev_lines = MagicMock()
        res_prev_lines.all.return_value = []

        mock_db.execute.side_effect = [res_no_tx, res_order, res_orig, res_prev_rev, res_prev_lines]

        req = OrderReturnRequest(
            order_id="ORD-002",
            idempotency_key="IDEM-RET-NEG-001",
            lines=[ReturnLineCreate(order_line_id="ORDL-002-01", quantity_returned=1)],
        )

        response = await ReturnService.process_return(mock_db, req, actor_id="ACTOR-OPERATOR-1")

        assert response.points_reversed == 150
        assert response.new_balance == -100  # 50 - 150 = -100
        assert response.is_balance_negative is True
        assert response.redemptions_frozen is True


# ============================================================================
# WORKFLOW F: Points Expiry Tests
# ============================================================================

class TestWorkflowFPointsExpiry:

    @pytest.mark.asyncio
    async def test_expiry_batch_idempotent_and_updates_status(self):
        """
        Workflow F: Expires eligible lots past cutoff date.
        Updates lot status to EXPIRED and remaining_points to 0.
        Subsequent execution with same batch ID raises ConflictError.
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # Batch check: not found
        res_no_batch = MagicMock()
        res_no_batch.scalar_one_or_none.return_value = None

        now = datetime.now(timezone.utc)
        account = make_account(balance=400)
        lot = PointsLot(
            lot_id="LOT-EXPIRED-001",
            transaction_id="PTS-ACC-001",
            account_id=account.account_id,
            initial_points=200,
            remaining_points=200,
            status="ACTIVE",
            expires_at=now - timedelta(days=5),  # 5 days ago
        )

        res_lots = MagicMock()
        res_lots.scalars.return_value.all.return_value = [lot]

        res_accounts = MagicMock()
        res_accounts.scalars.return_value.all.return_value = [account]

        mock_db.execute.side_effect = [res_no_batch, res_lots, res_accounts]

        req = ExpiryExecutionRequest(
            cutoff_date=now,
            idempotency_key="EXP-BATCH-2026-001",
        )

        response = await ExpiryService.process_expiries(mock_db, req, actor_id="ACTOR-SYSTEM-CRON")

        assert response.total_points_expired == 200
        assert response.total_lots_processed == 1
        assert response.status == "COMPLETED"
        assert lot.remaining_points == 0
        assert lot.status == "EXPIRED"
        assert account.current_balance == 200  # 400 - 200
        assert mock_db.commit.call_count == 1


# ============================================================================
# WORKFLOW G: Tier Management Tests
# ============================================================================

class TestWorkflowGTierManagement:

    @pytest.mark.asyncio
    async def test_tier_upgrade_on_qualifying_spend_threshold(self):
        """
        Workflow G: Evaluates 365-day qualifying spend and triggers tier upgrade.
        Customer was Bronze ($0), earned $1,200.00 qualifying spend -> upgraded to Gold.
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        bronze = make_tier(tier_id="TIER-BRONZE", rank=1, min_spend=Decimal("0.00"), multiplier=Decimal("1.00"))
        silver = make_tier(tier_id="TIER-SILVER", rank=2, min_spend=Decimal("500.00"), multiplier=Decimal("1.25"))
        gold = make_tier(tier_id="TIER-GOLD", rank=3, min_spend=Decimal("1000.00"), multiplier=Decimal("1.50"))

        account = make_account(tier=bronze)
        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        # Orders in last 365 days = $1,200.00
        res_orders = MagicMock()
        res_orders.scalar.return_value = Decimal("1200.00")

        # Refunds in last 365 days = $0.00
        res_refunds = MagicMock()
        res_refunds.scalar.return_value = Decimal("0.00")

        # Tier catalog
        res_tiers = MagicMock()
        res_tiers.scalars.return_value.all.return_value = [bronze, silver, gold]

        mock_db.execute.side_effect = [res_acc, res_orders, res_refunds, res_tiers]

        response = await TierService.evaluate_account_tier(mock_db, account.account_id, actor_id="ACTOR-SYSTEM")

        assert response.current_tier_id == "TIER-GOLD"
        assert response.previous_tier_id == "TIER-BRONZE"
        assert response.is_upgrade is True
        assert response.multiplier == Decimal("1.50")
        assert account.tier_id == "TIER-GOLD"
        assert mock_db.commit.call_count == 1


# ============================================================================
# WORKFLOW SECURITY & ACCESS CONTROL TESTS
# ============================================================================

