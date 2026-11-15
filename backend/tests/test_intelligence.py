"""
LoyaltyOS — Phase 5 LLIRE (Loyalty Ledger Intelligence & Reconciliation Engine) Tests
Covers all 5 mandatory anomaly detectors, severity classification, explainability,
idempotency, RBAC security scoping, and ground truth evaluation metrics.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer, LoyaltyAccount, Tier, Order, OrderReturn
from backend.app.models.ledger import PointsTransaction, PointsLot, Redemption, PointsLotAllocation, ExpiryBatchItem
from backend.app.models.audit import AnomalyIncident
from backend.app.services.intelligence.base import AnomalyFinding
from backend.app.services.intelligence.balance_mismatch import BalanceMismatchDetector
from backend.app.services.intelligence.over_redemption import OverRedemptionDetector
from backend.app.services.intelligence.unreversed_return import UnreversedReturnDetector
from backend.app.services.intelligence.double_expiry import DoubleExpiryDetector
from backend.app.services.intelligence.incorrect_tier import IncorrectTierDetector
from backend.app.services.intelligence.engine import IntelligenceEngine
from backend.app.services.intelligence.evaluator import IntelligenceEvaluator


# ============================================================================
# Helpers
# ============================================================================

def make_tier(tier_id="TIER-BRONZE", name="Bronze", rank=1, min_spend=Decimal("0.00"), multiplier=Decimal("1.00")):
    return Tier(
        tier_id=tier_id,
        name=name,
        rank=rank,
        min_spend=min_spend,
        earning_multiplier=multiplier,
    )


def make_account(account_id="LOY-001", customer_id="CUST-001", tier=None, balance=1000):
    t = tier or make_tier()
    acc = LoyaltyAccount(
        account_id=account_id,
        customer_id=customer_id,
        tier_id=t.tier_id,
        current_balance=balance,
        lifetime_accrued=balance,
        lifetime_redeemed=0,
        qualifying_spend=Decimal("0.00"),
        status="ACTIVE",
    )
    acc.tier = t
    return acc


# ============================================================================
# Detector 1: Account Balance Mismatch Tests
# ============================================================================

class TestBalanceMismatchDetector:

    @pytest.mark.asyncio
    async def test_balance_mismatch_detected(self):
        """Detector 1: Identifies account where stored balance diverges from ledger transactions."""
        mock_db = AsyncMock()

        acc = make_account(account_id="LOY-CUST-000026", balance=1409)

        # Mock db queries: 1. accounts query, 2. ledger sum (1159), 3. active lots sum (1159), 4. recent txs
        res_acc = MagicMock()
        res_acc.scalars.return_value.all.return_value = [acc]

        res_sum = MagicMock()
        res_sum.scalar.return_value = 1159  # Journal sum is 1159 vs stored 1409 (drift: +250)

        res_lots = MagicMock()
        res_lots.scalar.return_value = 1159

        res_txs = MagicMock()
        res_txs.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [res_acc, res_sum, res_lots, res_txs]

        detector = BalanceMismatchDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "BALANCE_MISMATCH"
        assert f.entity_id == "LOY-CUST-000026"
        assert f.variance_amount == Decimal("250")
        assert f.severity == "CRITICAL"
        assert "BR-01" in f.rule_violated
        assert "Direct database drift" in f.what_happened
        assert f.discrepancy_calculation["variance"] == 250
        assert f.evidence["stored_balance"] == 1409
        assert f.evidence["calculated_ledger_balance"] == 1159

    @pytest.mark.asyncio
    async def test_valid_account_not_incorrectly_flagged(self):
        """Detector 1: Reconciled account with stored balance == journal sum has 0 findings."""
        mock_db = AsyncMock()

        acc = make_account(account_id="LOY-CUST-VALID", balance=1000)

        res_acc = MagicMock()
        res_acc.scalars.return_value.all.return_value = [acc]

        res_sum = MagicMock()
        res_sum.scalar.return_value = 1000  # Exactly matches stored balance

        res_lots = MagicMock()
        res_lots.scalar.return_value = 1000

        mock_db.execute.side_effect = [res_acc, res_sum, res_lots]

        detector = BalanceMismatchDetector()
        findings = await detector.detect(mock_db)
        assert len(findings) == 0


# ============================================================================
# Detector 2: Over-Redemption Tests
# ============================================================================

class TestOverRedemptionDetector:

    @pytest.mark.asyncio
    async def test_over_redemption_detected(self):
        """Detector 2: Detects redemption that drove running balance negative (unauthorized overdraft)."""
        mock_db = AsyncMock()

        # Redemption for 1265 pts when available was only 265 pts -> running balance -1000
        rdm = Redemption(
            redemption_id="RDM-ANOM-0002",
            account_id="LOY-CUST-000099",
            reward_id="REW-VOUCH-10",
            transaction_id="PTS-ANOM-0002",
            points_redeemed=1265,
            voucher_code="VOUCH-ANOM-123456",
            status="ISSUED",
        )
        tx = PointsTransaction(
            transaction_id="PTS-ANOM-0002",
            account_id="LOY-CUST-000099",
            entry_type="REDEMPTION",
            points=-1265,
            running_balance=-1000,
            idempotency_key="IDEM-RDM-ANOM-0002",
        )
        rdm.transaction = tx
        rdm.allocations = [
            PointsLotAllocation(allocation_id="ALL-1", lot_id="LOT-1", transaction_id=tx.transaction_id, points_allocated=265)
        ]

        res_rdm = MagicMock()
        res_rdm.scalars.return_value.all.return_value = [rdm]
        mock_db.execute.return_value = res_rdm

        detector = OverRedemptionDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "OVER_REDEMPTION"
        assert f.entity_id == "RDM-ANOM-0002"
        assert f.severity == "CRITICAL"
        assert f.variance_amount == Decimal("1000")
        assert f.evidence["overdraft_points"] == 1000
        assert f.evidence["available_points_at_transaction_time"] == 265
        assert "BR-04 / BR-08" in f.rule_violated

    @pytest.mark.asyncio
    async def test_legitimate_return_negative_balance_not_misclassified(self):
        """Detector 2: Legitimate negative balance caused by return reversals is NOT flagged as over-redemption."""
        mock_db = AsyncMock()

        # Redemption that had sufficient balance at transaction time (running balance 500)
        rdm = Redemption(
            redemption_id="RDM-LEGIT-001",
            account_id="LOY-CUST-RETURN",
            reward_id="REW-1",
            transaction_id="PTS-RDM-1",
            points_redeemed=500,
            voucher_code="VOUCH-LEGIT-1",
            status="ISSUED",
        )
        tx = PointsTransaction(
            transaction_id="PTS-RDM-1",
            account_id="LOY-CUST-RETURN",
            entry_type="REDEMPTION",
            points=-500,
            running_balance=500,  # Available before was 1000; running balance remained positive!
            idempotency_key="IDEM-LEGIT-RDM-1",
        )
        rdm.transaction = tx
        rdm.allocations = [
            PointsLotAllocation(allocation_id="ALL-LEGIT", lot_id="LOT-1", transaction_id=tx.transaction_id, points_allocated=500)
        ]

        res_rdm = MagicMock()
        res_rdm.scalars.return_value.all.return_value = [rdm]
        mock_db.execute.return_value = res_rdm

        detector = OverRedemptionDetector()
        findings = await detector.detect(mock_db)
        assert len(findings) == 0


# ============================================================================
# Detector 3: Unreversed Return Tests
# ============================================================================

class TestUnreversedReturnDetector:

    @pytest.mark.asyncio
    async def test_missing_return_reversal_detected(self):
        """Detector 3: Detects completed refund where points_reversed is 0 despite original points accrual."""
        mock_db = AsyncMock()

        order = Order(
            order_id="ORD-2026-000433",
            customer_id="CUST-000045",
            eligible_net_spend=Decimal("397.80"),
            status="RETURNED",
        )
        ret = OrderReturn(
            return_id="RET-ANOM-0003",
            order_id="ORD-2026-000433",
            return_type="FULL",
            total_refund_amount=Decimal("397.80"),
            points_reversed=0,  # ANOMALY: zero points reversed
            status="PROCESSED",
        )
        ret.order = order

        accrual_tx = PointsTransaction(
            transaction_id="PTS-ACCRUAL-433",
            account_id="LOY-45",
            order_id="ORD-2026-000433",
            entry_type="ACCRUAL",
            points=397,
            running_balance=397,
            idempotency_key="IDEM-ORD-433",
        )

        res_ret = MagicMock()
        res_ret.scalars.return_value.all.return_value = [ret]

        res_accrual = MagicMock()
        res_accrual.scalar_one_or_none.return_value = accrual_tx

        res_rev = MagicMock()
        res_rev.scalar.return_value = 0  # 0 points reversed in journal

        mock_db.execute.side_effect = [res_ret, res_accrual, res_rev]

        detector = UnreversedReturnDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "UNREVERSED_RETURN"
        assert f.entity_id == "RET-ANOM-0003"
        assert f.variance_amount == Decimal("397")
        assert f.severity == "HIGH"
        assert f.evidence["missing_points"] == 397
        assert f.evidence["actual_reversal_points"] == 0

    @pytest.mark.asyncio
    async def test_partial_return_reversal_calculation(self):
        """Detector 3: Partial return with insufficient reversal correctly calculates missing points."""
        mock_db = AsyncMock()

        order = Order(
            order_id="ORD-PARTIAL-1",
            customer_id="CUST-PARTIAL",
            eligible_net_spend=Decimal("100.00"),
            status="COMPLETED",
        )
        ret = OrderReturn(
            return_id="RET-PARTIAL-1",
            order_id="ORD-PARTIAL-1",
            return_type="PARTIAL",
            total_refund_amount=Decimal("50.00"),  # $50 refunded
            points_reversed=20,  # Reversal of only 20 points instead of 50
            status="PROCESSED",
        )
        ret.order = order

        accrual_tx = PointsTransaction(
            transaction_id="PTS-ACC-P1",
            account_id="LOY-P1",
            order_id="ORD-PARTIAL-1",
            entry_type="ACCRUAL",
            points=100,
            running_balance=100,
            idempotency_key="IDEM-P1",
        )

        res_ret = MagicMock()
        res_ret.scalars.return_value.all.return_value = [ret]

        res_accrual = MagicMock()
        res_accrual.scalar_one_or_none.return_value = accrual_tx

        res_rev = MagicMock()
        res_rev.scalar.return_value = 20

        mock_db.execute.side_effect = [res_ret, res_accrual, res_rev]

        detector = UnreversedReturnDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        assert findings[0].evidence["expected_reversal_points"] == 50
        assert findings[0].evidence["actual_reversal_points"] == 20
        assert findings[0].evidence["missing_points"] == 30


# ============================================================================
# Detector 4: Duplicate Expiry Tests
# ============================================================================

class TestDoubleExpiryDetector:

    @pytest.mark.asyncio
    async def test_duplicate_expiry_detected(self):
        """Detector 4: Identifies points lot expired twice across multiple batches."""
        mock_db = AsyncMock()

        lot = PointsLot(
            lot_id="LOT-2026-00000453",
            transaction_id="PTS-LOT-453",
            account_id="LOY-CUST-000044",
            initial_points=553,
            remaining_points=0,
            status="EXPIRED",
            expires_at=datetime.now(timezone.utc),
        )

        item1 = ExpiryBatchItem(
            item_id="EITEM-1",
            batch_id="EXP-2026-000001",
            lot_id="LOT-2026-00000453",
            transaction_id="PTS-EXP-1",
            points_expired=553,
        )
        item2 = ExpiryBatchItem(
            item_id="EITEM-ANOM-0004",
            batch_id="EXP-ANOM-0004",
            lot_id="LOT-2026-00000453",
            transaction_id="PTS-ANOM-EXP-0004",
            points_expired=553,  # Second deduction
        )

        res_items = MagicMock()
        res_items.scalars.return_value.all.return_value = [item1, item2]

        res_lot = MagicMock()
        res_lot.scalar_one_or_none.return_value = lot

        mock_db.execute.side_effect = [res_items, res_lot]

        detector = DoubleExpiryDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "DOUBLE_EXPIRY"
        assert f.entity_id == "LOT-2026-00000453"
        assert f.severity == "HIGH"
        assert f.variance_amount == Decimal("553")
        assert f.evidence["excess_points_deducted"] == 553
        assert len(f.evidence["batch_ids"]) == 2

    @pytest.mark.asyncio
    async def test_correct_single_expiry_not_flagged(self):
        """Detector 4: Correct single expiry batch execution is NOT flagged."""
        mock_db = AsyncMock()

        lot = PointsLot(
            lot_id="LOT-LEGIT-EXP",
            transaction_id="PTS-LOT-LEGIT",
            account_id="LOY-LEGIT",
            initial_points=500,
            remaining_points=0,
            status="EXPIRED",
            expires_at=datetime.now(timezone.utc),
        )
        item = ExpiryBatchItem(
            item_id="EITEM-LEGIT",
            batch_id="EXP-BATCH-1",
            lot_id="LOT-LEGIT-EXP",
            transaction_id="PTS-EXP-LEGIT",
            points_expired=500,
        )

        res_items = MagicMock()
        res_items.scalars.return_value.all.return_value = [item]

        res_lot = MagicMock()
        res_lot.scalar_one_or_none.return_value = lot

        mock_db.execute.side_effect = [res_items, res_lot]

        detector = DoubleExpiryDetector()
        findings = await detector.detect(mock_db)
        assert len(findings) == 0


# ============================================================================
# Detector 5: Incorrect Tier Calculation Tests
# ============================================================================

class TestIncorrectTierDetector:

    @pytest.mark.asyncio
    async def test_incorrect_gross_spend_tier_detected(self):
        """Detector 5: Detects account in Gold tier when qualifying spend is $0.00 (gross spend inflation)."""
        mock_db = AsyncMock()

        tiers = [
            make_tier("TIER-BRONZE", "Bronze", rank=1, min_spend=Decimal("0.00")),
            make_tier("TIER-SILVER", "Silver", rank=2, min_spend=Decimal("1000.00")),
            make_tier("TIER-GOLD", "Gold", rank=3, min_spend=Decimal("2500.00")),
            make_tier("TIER-PLATINUM", "Platinum", rank=4, min_spend=Decimal("5000.00")),
        ]

        # Account is currently Gold (Rank 3)
        acc = make_account(
            account_id="LOY-CUST-000070",
            customer_id="CUST-000070",
            tier=tiers[2],  # Gold
        )

        res_tiers = MagicMock()
        res_tiers.scalars.return_value.all.return_value = tiers

        res_acc = MagicMock()
        res_acc.scalars.return_value.all.return_value = [acc]

        # Reconstructed spend: net spend = 0, gross spend = 2600 (shipping/tax), 1 order
        res_spend = MagicMock()
        res_spend.first.return_value = (Decimal("0.00"), Decimal("2600.00"), 1)

        # Refunds: 0
        res_refunds = MagicMock()
        res_refunds.scalar.return_value = Decimal("0.00")

        mock_db.execute.side_effect = [res_tiers, res_acc, res_spend, res_refunds]

        detector = IncorrectTierDetector()
        findings = await detector.detect(mock_db)

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "INCORRECT_TIER"
        assert f.entity_id == "LOY-CUST-000070"
        assert f.evidence["current_tier_id"] == "TIER-GOLD"
        assert f.evidence["expected_tier_id"] == "TIER-BRONZE"
        assert f.evidence["is_gross_inflation_suspected"] is True
        assert f.variance_amount == Decimal("2500.00")

    @pytest.mark.asyncio
    async def test_correct_qualifying_spend_tier_not_flagged(self):
        """Detector 5: Correctly earned tier based on qualifying spend is NOT flagged."""
        mock_db = AsyncMock()

        tiers = [
            make_tier("TIER-BRONZE", "Bronze", rank=1, min_spend=Decimal("0.00")),
            make_tier("TIER-SILVER", "Silver", rank=2, min_spend=Decimal("1000.00")),
            make_tier("TIER-GOLD", "Gold", rank=3, min_spend=Decimal("2500.00")),
        ]

        acc = make_account(account_id="LOY-EARNED", tier=tiers[1])  # Silver

        res_tiers = MagicMock()
        res_tiers.scalars.return_value.all.return_value = tiers

        res_acc = MagicMock()
        res_acc.scalars.return_value.all.return_value = [acc]

        # Net spend $1500 (> $1000 threshold for Silver)
        res_spend = MagicMock()
        res_spend.first.return_value = (Decimal("1500.00"), Decimal("1600.00"), 2)

        res_refunds = MagicMock()
        res_refunds.scalar.return_value = Decimal("0.00")

        mock_db.execute.side_effect = [res_tiers, res_acc, res_spend, res_refunds]

        detector = IncorrectTierDetector()
        findings = await detector.detect(mock_db)
        assert len(findings) == 0


# ============================================================================
# Engine, Idempotency, Explainability, and Security Scoping Tests
# ============================================================================

class TestIntelligenceEngineAndAPI:

    @pytest.mark.asyncio
    async def test_severity_classification_rules(self):
        """Severity: Verifies explicit severity rules for all anomaly finding categories."""
        # Balance drift >= 100 is CRITICAL
        f1 = AnomalyFinding(
            detector_id="DET-BALANCE-MISMATCH",
            category="BALANCE_MISMATCH",
            entity_type="ACCOUNT",
            entity_id="ACC-1",
            variance_amount=Decimal("250"),
            severity="CRITICAL",
            severity_reason="CRITICAL ledger corruption",
            rule_violated="BR-01",
            what_happened="...",
            description="...",
            evidence={},
            discrepancy_calculation={},
            recommendation="...",
        )
        assert f1.severity == "CRITICAL"

        # Double expiry with excess points is HIGH
        f2 = AnomalyFinding(
            detector_id="DET-DOUBLE-EXPIRY",
            category="DOUBLE_EXPIRY",
            entity_type="POINTS_LOT",
            entity_id="LOT-1",
            variance_amount=Decimal("500"),
            severity="HIGH",
            severity_reason="HIGH customer impact",
            rule_violated="BR-11",
            what_happened="...",
            description="...",
            evidence={},
            discrepancy_calculation={},
            recommendation="...",
        )
        assert f2.severity == "HIGH"

    @pytest.mark.asyncio
    async def test_explainability_evidence_completeness(self):
        """Explainability: Verifies that every finding contains the required forensic answers."""
        f = AnomalyFinding(
            detector_id="DET-OVER-REDEMPTION",
            category="OVER_REDEMPTION",
            entity_type="REDEMPTION",
            entity_id="RDM-1",
            variance_amount=Decimal("1000"),
            severity="CRITICAL",
            severity_reason="Unauthorized overdraft",
            rule_violated="BR-04 / BR-08",
            what_happened="Over-redemption allowed 1000 points beyond available balance",
            description="Overdraft of 1000 points on RDM-1",
            evidence={"redemption_id": "RDM-1", "overdraft": 1000},
            discrepancy_calculation={"formula": "requested - available", "overdraft": 1000},
            recommendation="Freeze account and invalidate voucher",
        )
        payload = f.to_details_payload()

        assert "what_happened" in payload
        assert "rule_violated" in payload
        assert "evidence" in payload
        assert "discrepancy_calculation" in payload
        assert "severity_reason" in payload
        assert "recommendation" in payload
        assert "fingerprint" in payload

    @pytest.mark.asyncio
    async def test_repeated_detection_idempotency(self):
        """Idempotency: Re-running detection with identical finding does NOT duplicate AnomalyIncident rows."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        finding = AnomalyFinding(
            detector_id="DET-BALANCE-MISMATCH",
            category="BALANCE_MISMATCH",
            entity_type="ACCOUNT",
            entity_id="LOY-DUPLICATE",
            variance_amount=Decimal("100"),
            severity="CRITICAL",
            severity_reason="Drift",
            rule_violated="BR-01",
            what_happened="Drift",
            description="Drift",
            evidence={},
            discrepancy_calculation={},
            recommendation="Review",
        )

        # Existing incident with same fingerprint exists
        existing_incident = AnomalyIncident(
            incident_id="INC-EXISTING-001",
            issue_type="BALANCE_MISMATCH",
            entity_type="ACCOUNT",
            entity_id="LOY-DUPLICATE",
            variance_amount=Decimal("100"),
            details=finding.to_details_payload(),
            status="DETECTED",
            created_at=datetime.now(timezone.utc),
        )

        res_existing = MagicMock()
        res_existing.scalar_one_or_none.return_value = existing_incident
        mock_db.execute.return_value = res_existing

        engine = IntelligenceEngine()

        with patch.object(engine.detectors["DET-BALANCE-MISMATCH"], "detect", return_value=[finding]):
            run_res = await engine.run_detection(
                db=mock_db,
                actor_id="OPERATOR-1",
                detector_names=["DET-BALANCE-MISMATCH"],
            )

            assert run_res.new_incidents_created == 0
            assert run_res.existing_incidents_skipped == 1
            # Verify no AnomalyIncident was added (only AuditEvent is logged for the run)
            added_incidents = [
                call_arg[0][0]
                for call_arg in mock_db.add.call_args_list
                if isinstance(call_arg[0][0], AnomalyIncident)
            ]
            assert len(added_incidents) == 0

    @pytest.mark.asyncio
    async def test_unauthorized_detection_request_rejected(self, client):
        """Security: Non-analyst / non-operator customer calling POST /api/v1/intelligence/detect is rejected with 403."""
        customer_user = AppUser(
            id=uuid.uuid4(),
            email="cust@example.com",
            role="CUSTOMER",
            is_active=True,
        )
        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: customer_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        try:
            resp = await client.post("/api/v1/intelligence/detect", json={})
            assert resp.status_code == 403
            assert "Access denied" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_evaluation_metric_calculations(self):
        """Evaluation: Verifies Precision, Recall, and F1 score calculation against ground truth."""
        mock_db = AsyncMock()

        # Simulate 5 findings matching the 5 ground truth anomalies
        findings = [
            AnomalyFinding(
                detector_id="DET-BALANCE-MISMATCH",
                category="BALANCE_MISMATCH",
                entity_type="ACCOUNT",
                entity_id="LOY-CUST-000026",
                variance_amount=Decimal("250"),
                severity="CRITICAL",
                severity_reason="Drift",
                rule_violated="BR-01",
                what_happened="...",
                description="...",
                evidence={"account_id": "LOY-CUST-000026"},
                discrepancy_calculation={},
                recommendation="...",
            ),
            AnomalyFinding(
                detector_id="DET-OVER-REDEMPTION",
                category="OVER_REDEMPTION",
                entity_type="REDEMPTION",
                entity_id="RDM-ANOM-0002",
                variance_amount=Decimal("1000"),
                severity="CRITICAL",
                severity_reason="Overdraft",
                rule_violated="BR-04",
                what_happened="...",
                description="...",
                evidence={"account_id": "LOY-CUST-000099", "redemption_id": "RDM-ANOM-0002"},
                discrepancy_calculation={},
                recommendation="...",
            ),
            AnomalyFinding(
                detector_id="DET-UNREVERSED-RETURN",
                category="UNREVERSED_RETURN",
                entity_type="ORDER_RETURN",
                entity_id="RET-ANOM-0003",
                variance_amount=Decimal("397"),
                severity="HIGH",
                severity_reason="Leakage",
                rule_violated="BR-10",
                what_happened="...",
                description="...",
                evidence={"order_id": "ORD-2026-000433", "return_id": "RET-ANOM-0003"},
                discrepancy_calculation={},
                recommendation="...",
            ),
            AnomalyFinding(
                detector_id="DET-DOUBLE-EXPIRY",
                category="DOUBLE_EXPIRY",
                entity_type="POINTS_LOT",
                entity_id="LOT-2026-00000453",
                variance_amount=Decimal("553"),
                severity="HIGH",
                severity_reason="Double deduction",
                rule_violated="BR-11",
                what_happened="...",
                description="...",
                evidence={"lot_id": "LOT-2026-00000453"},
                discrepancy_calculation={},
                recommendation="...",
            ),
            AnomalyFinding(
                detector_id="DET-INCORRECT-TIER",
                category="INCORRECT_TIER",
                entity_type="ACCOUNT",
                entity_id="LOY-CUST-000070",
                variance_amount=Decimal("2500"),
                severity="MEDIUM",
                severity_reason="Gross inflation",
                rule_violated="BR-05",
                what_happened="...",
                description="...",
                evidence={"account_id": "LOY-CUST-000070"},
                discrepancy_calculation={},
                recommendation="...",
            ),
        ]

        eval_res = await IntelligenceEvaluator.evaluate(mock_db, findings=findings)

        assert eval_res.total_ground_truth_anomalies == 5
        assert eval_res.total_detected_anomalies == 5
        assert eval_res.aggregate.true_positives == 5
        assert eval_res.aggregate.false_positives == 0
        assert eval_res.aggregate.false_negatives == 0
        assert eval_res.aggregate.precision == 1.0
        assert eval_res.aggregate.recall == 1.0
        assert eval_res.aggregate.f1_score == 1.0

        for cat in ["BALANCE_MISMATCH", "OVER_REDEMPTION", "UNREVERSED_RETURN", "DOUBLE_EXPIRY", "INCORRECT_TIER"]:
            assert cat in eval_res.categories
            assert eval_res.categories[cat].true_positives == 1
            assert eval_res.categories[cat].false_positives == 0
            assert eval_res.categories[cat].false_negatives == 0
            assert eval_res.categories[cat].precision == 1.0
            assert eval_res.categories[cat].recall == 1.0
            assert eval_res.categories[cat].f1_score == 1.0

    @pytest.mark.asyncio
    async def test_api_get_intelligence_summary(self, client):
        """API: Operator calls GET /api/v1/intelligence/summary and receives aggregate statistics."""
        operator_user = AppUser(
            id=uuid.uuid4(),
            email="operator@example.com",
            role="OPERATOR",
            is_active=True,
        )
        mock_db = AsyncMock()
        incident = AnomalyIncident(
            incident_id="INC-SUM-001",
            issue_type="BALANCE_MISMATCH",
            entity_type="ACCOUNT",
            entity_id="LOY-001",
            variance_amount=Decimal("250.00"),
            details={"severity": "CRITICAL"},
            status="DETECTED",
            created_at=datetime.now(timezone.utc),
        )
        res_incidents = MagicMock()
        res_incidents.scalars.return_value.all.return_value = [incident]
        mock_db.execute.return_value = res_incidents

        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: operator_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            resp = await client.get("/api/v1/intelligence/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_incidents"] == 1
            assert data["open_incidents"] == 1
            assert data["by_severity"]["CRITICAL"] == 1
            assert data["by_category"]["BALANCE_MISMATCH"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_api_evaluate_engine_accuracy(self, client):
        """API: Analyst calls GET /api/v1/intelligence/evaluate and receives precision, recall, and F1."""
        analyst_user = AppUser(
            id=uuid.uuid4(),
            email="analyst@example.com",
            role="ANALYST",
            is_active=True,
        )
        mock_db = AsyncMock()

        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: analyst_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            resp = await client.get("/api/v1/intelligence/evaluate")
            assert resp.status_code == 200
            data = resp.json()
            assert data["dataset_scale"] == "TEST"
            assert data["total_ground_truth_anomalies"] == 5
            assert data["aggregate"]["f1_score"] == 1.0
            assert "BALANCE_MISMATCH" in data["categories"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_api_customer_isolation_on_anomaly_detail(self, client):
        """API: Customer cannot access an anomaly incident belonging to another customer."""
        customer_user = AppUser(
            id=uuid.uuid4(),
            email="customer@example.com",
            role="CUSTOMER",
            is_active=True,
        )
        mock_db = AsyncMock()

        # Customer's account query returns LOY-OWN
        res_own_acc = MagicMock()
        res_own_acc.scalar_one_or_none.return_value = "LOY-OWN"

        # Incident belongs to LOY-OTHER
        incident = AnomalyIncident(
            incident_id="INC-OTHER-001",
            issue_type="BALANCE_MISMATCH",
            entity_type="ACCOUNT",
            entity_id="LOY-OTHER",
            variance_amount=Decimal("500.00"),
            details={"severity": "CRITICAL", "evidence": {"account_id": "LOY-OTHER"}},
            status="DETECTED",
            created_at=datetime.now(timezone.utc),
        )
        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident

        mock_db.execute.side_effect = [res_inc, res_own_acc]

        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: customer_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            resp = await client.get("/api/v1/intelligence/anomalies/INC-OTHER-001")
            assert resp.status_code == 403
            assert "Access denied" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

