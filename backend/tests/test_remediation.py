"""
LoyaltyOS — Phase 6 Controlled Remediation & Dual-Key Approval Engine Tests
Tests the full lifecycle:
LLIRE finding -> Investigation -> Action Proposal -> Dual-Key Approval ->
Compensating Ledger Transaction -> Ledger Reconciliation -> Forensic Audit.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer, LoyaltyAccount, Tier
from backend.app.models.ledger import PointsTransaction, PointsLot
from backend.app.models.audit import AnomalyIncident, CorrectiveAction
from backend.app.schemas.remediation import (
    InvestigationOpenRequest,
    InvestigationNoteRequest,
    CorrectiveActionProposalRequest,
    ApprovalDecisionRequest,
)
from backend.app.services.remediation_service import RemediationService
from backend.app.core.errors import (
    NotFoundError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
)


# ============================================================================
# Helpers
# ============================================================================

def make_tier():
    return Tier(
        tier_id="TIER-BRONZE",
        name="Bronze",
        rank=1,
        min_spend=Decimal("0.00"),
        earning_multiplier=Decimal("1.00"),
    )


def make_account(account_id="LOY-001", customer_id="CUST-001", balance=1409):
    acc = LoyaltyAccount(
        account_id=account_id,
        customer_id=customer_id,
        tier_id="TIER-BRONZE",
        current_balance=balance,
        lifetime_accrued=balance,
        lifetime_redeemed=0,
        qualifying_spend=Decimal("0.00"),
        status="ACTIVE",
    )
    acc.tier = make_tier()
    return acc


def make_incident(incident_id="INC-20261115-001", status="DETECTED", issue_type="BALANCE_MISMATCH", variance=Decimal("250.00"), account_id="LOY-001"):
    return AnomalyIncident(
        incident_id=incident_id,
        issue_type=issue_type,
        entity_type="ACCOUNT",
        entity_id=account_id,
        variance_amount=variance,
        details={
            "severity": "CRITICAL",
            "evidence": {"account_id": account_id, "customer_id": "CUST-001"},
            "investigation_state": status,
        },
        status=status,
        created_at=datetime.now(timezone.utc),
    )


# ============================================================================
# 1. Investigation Workflow Tests
# ============================================================================

class TestInvestigationWorkflow:

    @pytest.mark.asyncio
    async def test_investigation_creation_and_status_transition(self):
        """Investigation: Opening an investigation transitions status from DETECTED to INVESTIGATING."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        incident = make_incident(status="DETECTED")
        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        detail = await RemediationService.open_investigation(
            db=mock_db,
            incident_id="INC-20261115-001",
            actor_id="USER-ANALYST-1",
            notes="Initial triage confirms +250 drift.",
        )

        assert incident.status == "INVESTIGATING"
        assert incident.details["investigator_id"] == "USER-ANALYST-1"
        assert incident.details["investigation_state"] == "INVESTIGATING"
        assert len(incident.details["notes_history"]) == 1
        assert incident.details["notes_history"][0]["note"] == "Initial triage confirms +250 drift."
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_invalid_status_transition_on_resolved_incident(self):
        """Investigation: Attempting to reopen or modify a RESOLVED incident raises ConflictError."""
        mock_db = AsyncMock()
        resolved_incident = make_incident(status="RESOLVED")

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = resolved_incident
        mock_db.execute.return_value = res_inc

        with pytest.raises(ConflictError) as exc_info:
            await RemediationService.open_investigation(
                db=mock_db,
                incident_id="INC-20261115-001",
                actor_id="USER-ANALYST-1",
            )
        assert "already resolved" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_add_investigation_notes(self):
        """Investigation: Adding forensic notes records timestamped observation to history."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        incident = make_incident(status="INVESTIGATING")
        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        detail = await RemediationService.add_investigation_note(
            db=mock_db,
            incident_id="INC-20261115-001",
            actor_id="USER-OPERATOR-1",
            note_text="Audit log reveals manual SQL update without corresponding transaction.",
        )

        notes = incident.details["notes_history"]
        assert len(notes) == 1
        assert "manual SQL update" in notes[0]["note"]
        assert notes[0]["author"] == "USER-OPERATOR-1"


# ============================================================================
# 2. Corrective Action Proposal & Validation Tests
# ============================================================================

class TestCorrectiveActionProposal:

    @pytest.mark.asyncio
    async def test_propose_corrective_action_credit(self):
        """Proposal: Operator proposes ADJUSTMENT_CREDIT creating PENDING_APPROVAL action."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        incident = make_incident(status="INVESTIGATING")

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = CorrectiveActionProposalRequest(
            action_type="ADJUSTMENT_CREDIT",
            proposed_points=250,
            reason="Compensating credit to restore ledger double-entry parity.",
        )

        resp = await RemediationService.propose_corrective_action(
            db=mock_db,
            incident_id="INC-20261115-001",
            actor_id="PROPOSER-USER-1",
            req=req,
        )

        assert resp.action_type == "ADJUSTMENT_CREDIT"
        assert resp.proposed_points == 250
        assert resp.proposed_by == "PROPOSER-USER-1"
        assert resp.approval_status == "PENDING_APPROVAL"
        assert resp.execution_status == "PENDING"
        assert incident.details["active_proposal"]["action_type"] == "ADJUSTMENT_CREDIT"

    @pytest.mark.asyncio
    async def test_propose_action_invalid_points(self):
        """Proposal: Proposing credit or debit with zero or negative points is rejected."""
        mock_db = AsyncMock()
        incident = make_incident(status="INVESTIGATING")
        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = CorrectiveActionProposalRequest(
            action_type="ADJUSTMENT_CREDIT",
            proposed_points=0,
            reason="Zero adjustment.",
        )

        with pytest.raises(BadRequestError):
            await RemediationService.propose_corrective_action(
                db=mock_db,
                incident_id="INC-20261115-001",
                actor_id="PROPOSER-USER-1",
                req=req,
            )


# ============================================================================
# 3. Dual-Key Approval & Self-Approval Prevention Tests
# ============================================================================

class TestDualKeyApproval:

    @pytest.mark.asyncio
    async def test_self_approval_strictly_rejected(self):
        """Dual-Key: The proposer CANNOT approve their own corrective action (403 Forbidden)."""
        mock_db = AsyncMock()
        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-001",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-OPERATOR-SAME",
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "approval_status": "PENDING_APPROVAL",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = ApprovalDecisionRequest(decision="APPROVED", notes="I approve my own proposal.")

        with pytest.raises(ForbiddenError) as exc_info:
            await RemediationService.review_proposal(
                db=mock_db,
                incident_id=incident.incident_id,
                approver_id="USER-OPERATOR-SAME",  # Same user ID!
                approver_role="OPERATIONS_MANAGER",
                req=req,
            )
        assert "cannot approve your own" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_unauthorized_role_approval_rejected(self):
        """Dual-Key: Non-manager / non-permitted role cannot approve actions (403 Forbidden)."""
        mock_db = AsyncMock()
        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-001",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "PENDING_APPROVAL",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = ApprovalDecisionRequest(decision="APPROVED")

        with pytest.raises(ForbiddenError):
            await RemediationService.review_proposal(
                db=mock_db,
                incident_id=incident.incident_id,
                approver_id="USER-CUSTOMER-OR-ANALYST",
                approver_role="CUSTOMER",
                req=req,
            )

    @pytest.mark.asyncio
    async def test_rejection_requires_mandatory_reason(self):
        """Dual-Key: Rejecting a proposal without a documented reason raises BadRequestError."""
        mock_db = AsyncMock()
        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-001",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "PENDING_APPROVAL",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = ApprovalDecisionRequest(decision="REJECTED", rejection_reason=None, notes=None)

        with pytest.raises(BadRequestError) as exc_info:
            await RemediationService.review_proposal(
                db=mock_db,
                incident_id=incident.incident_id,
                approver_id="USER-MANAGER-2",
                approver_role="OPERATIONS_MANAGER",
                req=req,
            )
        assert "mandatory" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_rejected_action_creates_no_ledger_transaction(self):
        """Dual-Key: A rejected proposal records the rejection but NEVER creates a PointsTransaction."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-001",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "PENDING_APPROVAL",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = ApprovalDecisionRequest(decision="REJECTED", rejection_reason="Insufficient forensic evidence.")

        resp = await RemediationService.review_proposal(
            db=mock_db,
            incident_id=incident.incident_id,
            approver_id="USER-MANAGER-2",
            approver_role="OPERATIONS_MANAGER",
            req=req,
        )

        assert resp.approval_status == "REJECTED"
        assert resp.rejection_reason == "Insufficient forensic evidence."
        assert resp.execution_status == "FAILED"
        assert resp.compensating_transaction_id is None

        # Verify no PointsTransaction was added
        added_txs = [
            call_arg[0][0]
            for call_arg in mock_db.add.call_args_list
            if isinstance(call_arg[0][0], PointsTransaction)
        ]
        assert len(added_txs) == 0

    @pytest.mark.asyncio
    async def test_second_person_approval_and_idempotency(self):
        """Dual-Key: Authorized distinct Operations Manager approves action idempotently."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-001",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "PENDING_APPROVAL",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        req = ApprovalDecisionRequest(
            decision="APPROVED",
            notes="Audit verified discrepancy.",
            execute_immediately=False,
        )

        resp = await RemediationService.review_proposal(
            db=mock_db,
            incident_id=incident.incident_id,
            approver_id="USER-MANAGER-DISTINCT",
            approver_role="OPERATIONS_MANAGER",
            req=req,
        )

        assert resp.approval_status == "APPROVED"
        assert resp.approver_id == "USER-MANAGER-DISTINCT"

        # Re-evaluating identical approval returns idempotent response
        resp2 = await RemediationService.review_proposal(
            db=mock_db,
            incident_id=incident.incident_id,
            approver_id="USER-MANAGER-DISTINCT",
            approver_role="OPERATIONS_MANAGER",
            req=req,
        )
        assert resp2.approval_status == "APPROVED"


# ============================================================================
# 4. Safe Ledger Remediation & Post-Reconciliation Verification Tests
# ============================================================================

class TestSafeLedgerRemediation:

    @pytest.mark.asyncio
    async def test_approved_credit_adjustment_and_reconciliation_success(self):
        """Remediation: Approved credit posts transaction, updates balance, reconciles, and resolves incident."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        account = make_account(account_id="LOY-001", balance=1159)
        incident = make_incident(status="INVESTIGATING", account_id="LOY-001")
        incident.details["active_proposal"] = {
            "action_id": "ACT-CREDIT-001",
            "incident_id": incident.incident_id,
            "account_id": "LOY-001",
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "APPROVED",
            "approver_id": "USER-MANAGER",
            "execution_status": "PENDING",
            "reason": "Compensating credit",
        }

        # DB queries: 1. incident, 2. account with_for_update, 3. corrective_action lookup, 4. ledger sum (1409)
        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident

        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_corr = MagicMock()
        res_corr.scalar_one_or_none.return_value = CorrectiveAction(
            action_id="ACT-CREDIT-001",
            incident_id=incident.incident_id,
            operator_id="USER-MANAGER",
            decision="APPROVED",
        )

        res_sum = MagicMock()
        res_sum.scalar.return_value = 1409  # After +250, ledger sum is 1409 == stored 1409 (Reconciled!)

        mock_db.execute.side_effect = [res_inc, res_acc, res_corr, res_sum]

        resp = await RemediationService.execute_approved_action(
            db=mock_db,
            incident_id=incident.incident_id,
            actor_id="USER-MANAGER",
        )

        assert resp.execution_status == "EXECUTED"
        assert resp.reconciliation_status == "RECONCILED"
        assert account.current_balance == 1409  # 1159 + 250
        assert incident.status == "RESOLVED"
        assert incident.resolved_at is not None

        # Verify PointsTransaction was created
        added_txs = [
            call_arg[0][0]
            for call_arg in mock_db.add.call_args_list
            if isinstance(call_arg[0][0], PointsTransaction)
        ]
        assert len(added_txs) == 1
        tx = added_txs[0]
        assert tx.entry_type == "ADJUSTMENT_CREDIT"
        assert tx.points == 250
        assert tx.running_balance == 1409

    @pytest.mark.asyncio
    async def test_approved_debit_adjustment(self):
        """Remediation: Approved debit posts negative PointsTransaction and debits account balance."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        account = make_account(account_id="LOY-001", balance=1000)
        incident = make_incident(status="INVESTIGATING", account_id="LOY-001")
        incident.details["active_proposal"] = {
            "action_id": "ACT-DEBIT-001",
            "incident_id": incident.incident_id,
            "account_id": "LOY-001",
            "action_type": "ADJUSTMENT_DEBIT",
            "proposed_points": 100,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "APPROVED",
            "approver_id": "USER-MANAGER",
            "execution_status": "PENDING",
            "reason": "Compensating debit",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident

        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_corr = MagicMock()
        res_corr.scalar_one_or_none.return_value = None

        res_sum = MagicMock()
        res_sum.scalar.return_value = 900  # Reconciled at 900

        mock_db.execute.side_effect = [res_inc, res_acc, res_corr, res_sum]

        resp = await RemediationService.execute_approved_action(
            db=mock_db,
            incident_id=incident.incident_id,
            actor_id="USER-MANAGER",
        )

        assert resp.execution_status == "EXECUTED"
        assert account.current_balance == 900

        added_txs = [
            call_arg[0][0]
            for call_arg in mock_db.add.call_args_list
            if isinstance(call_arg[0][0], PointsTransaction)
        ]
        assert len(added_txs) == 1
        assert added_txs[0].entry_type == "ADJUSTMENT_DEBIT"
        assert added_txs[0].points == -100

    @pytest.mark.asyncio
    async def test_finding_remains_open_when_reconciliation_fails(self):
        """Remediation: If post-correction ledger reconciliation still exhibits drift, incident stays INVESTIGATING."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        account = make_account(account_id="LOY-001", balance=1500)
        incident = make_incident(status="INVESTIGATING", account_id="LOY-001")
        incident.details["active_proposal"] = {
            "action_id": "ACT-PARTIAL-001",
            "incident_id": incident.incident_id,
            "account_id": "LOY-001",
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 100,  # Only partial credit of 100
            "proposed_by": "USER-PROPOSER",
            "approval_status": "APPROVED",
            "approver_id": "USER-MANAGER",
            "execution_status": "PENDING",
            "reason": "Partial credit",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident

        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_corr = MagicMock()
        res_corr.scalar_one_or_none.return_value = None

        res_sum = MagicMock()
        res_sum.scalar.return_value = 1200  # Stored is 1600 (1500+100), but ledger sum is only 1200 (drift 400!)

        mock_db.execute.side_effect = [res_inc, res_acc, res_corr, res_sum]

        resp = await RemediationService.execute_approved_action(
            db=mock_db,
            incident_id=incident.incident_id,
            actor_id="USER-MANAGER",
        )

        assert resp.execution_status == "EXECUTED"
        assert resp.reconciliation_status == "DISCREPANCY_PERSISTS"
        assert incident.status == "INVESTIGATING"  # Does NOT mark resolved!
        assert incident.resolved_at is None
        assert incident.details["remaining_discrepancy"] == 400

    @pytest.mark.asyncio
    async def test_duplicate_execution_prevented(self):
        """Remediation: An action already marked EXECUTED cannot be re-executed."""
        mock_db = AsyncMock()
        incident = make_incident(status="INVESTIGATING")
        incident.details["active_proposal"] = {
            "action_id": "ACT-ALREADY-DONE",
            "incident_id": incident.incident_id,
            "action_type": "ADJUSTMENT_CREDIT",
            "proposed_points": 250,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "APPROVED",
            "execution_status": "EXECUTED",  # Already executed
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident
        mock_db.execute.return_value = res_inc

        resp = await RemediationService.execute_approved_action(
            db=mock_db,
            incident_id=incident.incident_id,
            actor_id="USER-MANAGER",
        )
        # Returns idempotent response without adding new transactions
        assert resp.execution_status == "EXECUTED"
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_account_freeze_and_unfreeze_actions(self):
        """Remediation: ACCOUNT_FREEZE sets account status to FROZEN; ACCOUNT_UNFREEZE sets to ACTIVE."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        account = make_account(account_id="LOY-FREEZE", balance=500)
        incident = make_incident(status="INVESTIGATING", account_id="LOY-FREEZE")
        incident.details["active_proposal"] = {
            "action_id": "ACT-FRZ-001",
            "incident_id": incident.incident_id,
            "account_id": "LOY-FREEZE",
            "action_type": "ACCOUNT_FREEZE",
            "proposed_points": 0,
            "proposed_by": "USER-PROPOSER",
            "approval_status": "APPROVED",
            "execution_status": "PENDING",
            "reason": "Suspicious over-redemption activity",
        }

        res_inc = MagicMock()
        res_inc.scalar_one_or_none.return_value = incident

        res_acc = MagicMock()
        res_acc.scalar_one_or_none.return_value = account

        res_corr = MagicMock()
        res_corr.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [res_inc, res_acc, res_corr]

        resp = await RemediationService.execute_approved_action(
            db=mock_db,
            incident_id=incident.incident_id,
            actor_id="USER-MANAGER",
        )

        assert resp.execution_status == "EXECUTED"
        assert account.status == "FROZEN"


# ============================================================================
# 5. REST API Security & Endpoint Integration Tests
# ============================================================================

class TestRemediationAPIEndpoints:

    @pytest.mark.asyncio
    async def test_api_list_findings_awaiting_investigation(self, client):
        """API: Operator calls GET /api/v1/corrective-actions/findings-awaiting-investigation."""
        operator_user = AppUser(id=uuid.uuid4(), email="op@example.com", role="OPERATOR", is_active=True)
        mock_db = AsyncMock()
        incident = make_incident(status="DETECTED")

        res = MagicMock()
        res.scalars.return_value.all.return_value = [incident]
        mock_db.execute.return_value = res

        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: operator_user
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            resp = await client.get("/api/v1/corrective-actions/findings-awaiting-investigation")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["incident_id"] == "INC-20261115-001"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_api_customer_forbidden_from_remediation(self, client):
        """API: Customer role attempting to access remediation endpoints is rejected with HTTP 403."""
        customer_user = AppUser(id=uuid.uuid4(), email="cust@example.com", role="CUSTOMER", is_active=True)
        from backend.app.api.deps import get_current_user, get_db
        from backend.app.main import app

        app.dependency_overrides[get_current_user] = lambda: customer_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        try:
            resp = await client.get("/api/v1/corrective-actions/findings-awaiting-investigation")
            assert resp.status_code == 403
            assert "Access denied" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()
