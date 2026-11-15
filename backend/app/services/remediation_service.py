import uuid
import math
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AnomalyIncident, CorrectiveAction
from backend.app.models.loyalty import LoyaltyAccount, Customer, Order
from backend.app.models.ledger import PointsTransaction, PointsLot
from backend.app.schemas.remediation import (
    CorrectiveActionProposalRequest,
    ApprovalDecisionRequest,
    CorrectiveActionResponse,
    CorrectiveActionListPage,
    InvestigationDetailResponse,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.ledger_service import LedgerService
from backend.app.core.errors import (
    NotFoundError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
)
from backend.app.core.logging import logger


class RemediationService:
    """
    Phase 6: Controlled Remediation & Dual-Key Approval Engine.
    Orchestrates the complete lifecycle:
    LLIRE Finding -> Investigation -> Proposed Action -> Dual-Key Approval ->
    Compensating Ledger Transaction -> Ledger Reconciliation -> Forensic Audit.
    Strictly forbids self-approval, silent modifications, and unauthorized balance updates.
    """

    SUPPORTED_ACTIONS = {
        "ADJUSTMENT_CREDIT",
        "ADJUSTMENT_DEBIT",
        "REVERSAL_REVIEW",
        "ACCOUNT_FREEZE",
        "ACCOUNT_UNFREEZE",
        "DISMISS_FINDING",
    }

    @classmethod
    async def _resolve_account_id(cls, db: AsyncSession, incident: AnomalyIncident) -> Optional[str]:
        """Resolves target account_id across any anomaly entity type."""
        details = incident.details or {}
        evidence = details.get("evidence", {})
        if "account_id" in evidence:
            return evidence["account_id"]

        if incident.entity_type == "ACCOUNT":
            return incident.entity_id

        if incident.entity_type == "ORDER_RETURN" or incident.entity_type == "ORDER":
            order_id = evidence.get("order_id") or incident.entity_id
            order_stmt = select(Order).where(Order.order_id == order_id)
            order = (await db.execute(order_stmt)).scalar_one_or_none()
            if order:
                acc_stmt = select(LoyaltyAccount.account_id).where(LoyaltyAccount.customer_id == order.customer_id)
                return (await db.execute(acc_stmt)).scalar_one_or_none()

        if incident.entity_type == "POINTS_LOT":
            lot_stmt = select(PointsLot.account_id).where(PointsLot.lot_id == incident.entity_id)
            return (await db.execute(lot_stmt)).scalar_one_or_none()

        return None

    @classmethod
    def _proposal_to_response(cls, incident: AnomalyIncident, proposal: Dict[str, Any]) -> CorrectiveActionResponse:
        return CorrectiveActionResponse(
            action_id=proposal["action_id"],
            incident_id=incident.incident_id,
            account_id=proposal.get("account_id"),
            customer_id=proposal.get("customer_id"),
            action_type=proposal["action_type"],
            proposed_points=proposal.get("proposed_points", 0),
            proposed_by=proposal["proposed_by"],
            proposed_at=datetime.fromisoformat(proposal["proposed_at"]) if isinstance(proposal.get("proposed_at"), str) else proposal.get("proposed_at", datetime.now(timezone.utc)),
            approval_status=proposal.get("approval_status", "PENDING_APPROVAL"),
            approver_id=proposal.get("approver_id"),
            approved_at=datetime.fromisoformat(proposal["approved_at"]) if isinstance(proposal.get("approved_at"), str) else proposal.get("approved_at"),
            rejection_reason=proposal.get("rejection_reason"),
            execution_status=proposal.get("execution_status", "PENDING"),
            executed_at=datetime.fromisoformat(proposal["executed_at"]) if isinstance(proposal.get("executed_at"), str) else proposal.get("executed_at"),
            compensating_transaction_id=proposal.get("compensating_transaction_id"),
            reconciliation_status=proposal.get("reconciliation_status"),
            reconciliation_details=proposal.get("reconciliation_details"),
            notes=proposal.get("reason"),
        )

    @classmethod
    async def list_awaiting_investigation(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[AnomalyIncident]:
        query = select(AnomalyIncident)
        if status:
            query = query.where(AnomalyIncident.status == status.upper().strip())
        else:
            query = query.where(AnomalyIncident.status.in_(["DETECTED", "INVESTIGATING"]))

        query = query.order_by(desc(AnomalyIncident.created_at)).offset((page - 1) * page_size).limit(page_size)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_investigation_detail(
        cls,
        db: AsyncSession,
        incident_id: str,
    ) -> InvestigationDetailResponse:
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        details = dict(incident.details or {})
        active_prop_data = details.get("active_proposal")
        active_prop_resp = cls._proposal_to_response(incident, active_prop_data) if active_prop_data else None

        return InvestigationDetailResponse(
            incident_id=incident.incident_id,
            issue_type=incident.issue_type,
            entity_type=incident.entity_type,
            entity_id=incident.entity_id,
            variance_amount=incident.variance_amount,
            status=incident.status,
            investigator_id=details.get("investigator_id"),
            investigation_state=details.get("investigation_state", "DETECTED"),
            notes_history=details.get("notes_history", []),
            active_proposal=active_prop_resp,
            incident_details=details,
            created_at=incident.created_at,
            resolved_at=incident.resolved_at,
        )

    @classmethod
    async def open_investigation(
        cls,
        db: AsyncSession,
        incident_id: str,
        actor_id: str,
        investigator_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> InvestigationDetailResponse:
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        if incident.status in ("RESOLVED", "DISMISSED"):
            raise ConflictError(detail=f"Cannot open investigation on an already {incident.status.lower()} incident.")

        assigned_investigator = investigator_id or actor_id
        now = datetime.now(timezone.utc)

        # Update details payload
        details = dict(incident.details or {})
        details["investigator_id"] = assigned_investigator
        details["investigation_state"] = "INVESTIGATING"
        details["assigned_at"] = now.isoformat()

        notes_history = details.get("notes_history", [])
        if notes:
            notes_history.append({
                "author": actor_id,
                "timestamp": now.isoformat(),
                "note": notes,
                "type": "INITIAL_OBSERVATION",
            })
        details["notes_history"] = notes_history

        incident.status = "INVESTIGATING"
        incident.details = details

        await db.commit()

        # Audit event
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="INVESTIGATION_OPENED",
            entity_type="ANOMALY_INCIDENT",
            entity_id=incident_id,
            metadata={
                "incident_id": incident_id,
                "investigator_id": assigned_investigator,
                "status": "INVESTIGATING",
            },
        )

        return await cls.get_investigation_detail(db, incident_id)

    @classmethod
    async def add_investigation_note(
        cls,
        db: AsyncSession,
        incident_id: str,
        actor_id: str,
        note_text: str,
    ) -> InvestigationDetailResponse:
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        now = datetime.now(timezone.utc)
        details = dict(incident.details or {})
        notes_history = details.get("notes_history", [])
        notes_history.append({
            "author": actor_id,
            "timestamp": now.isoformat(),
            "note": note_text.strip(),
            "type": "INVESTIGATION_NOTE",
        })
        details["notes_history"] = notes_history
        incident.details = details

        await db.commit()

        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="INVESTIGATION_NOTE_ADDED",
            entity_type="ANOMALY_INCIDENT",
            entity_id=incident_id,
            metadata={"incident_id": incident_id, "note": note_text[:100]},
        )

        return await cls.get_investigation_detail(db, incident_id)

    @classmethod
    async def propose_corrective_action(
        cls,
        db: AsyncSession,
        incident_id: str,
        actor_id: str,
        req: CorrectiveActionProposalRequest,
    ) -> CorrectiveActionResponse:
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        if incident.status == "RESOLVED":
            raise ConflictError(detail="Cannot propose a corrective action for an already resolved incident.")

        action_type = req.action_type.upper().strip()
        if action_type not in cls.SUPPORTED_ACTIONS:
            raise BadRequestError(detail=f"Unsupported action type '{action_type}'. Supported: {', '.join(sorted(cls.SUPPORTED_ACTIONS))}.")

        # Financial adjustment validation
        if action_type in ("ADJUSTMENT_CREDIT", "ADJUSTMENT_DEBIT"):
            if not req.proposed_points or req.proposed_points <= 0:
                raise BadRequestError(detail=f"{action_type} requires a positive non-zero points adjustment amount.")

        # Account resolution
        account_id = await cls._resolve_account_id(db, incident)
        if not account_id and action_type in ("ADJUSTMENT_CREDIT", "ADJUSTMENT_DEBIT", "ACCOUNT_FREEZE", "ACCOUNT_UNFREEZE"):
            raise BadRequestError(detail=f"Cannot execute {action_type}: unable to resolve target loyalty account.")

        now = datetime.now(timezone.utc)
        action_id = f"ACT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        proposal_data = {
            "action_id": action_id,
            "incident_id": incident.incident_id,
            "account_id": account_id,
            "customer_id": (incident.details or {}).get("evidence", {}).get("customer_id"),
            "action_type": action_type,
            "proposed_points": req.proposed_points or 0,
            "reason": req.reason.strip(),
            "evidence_references": req.evidence_references or {},
            "proposed_by": actor_id,
            "proposed_at": now.isoformat(),
            "approval_status": "PENDING_APPROVAL",
            "approver_id": None,
            "approved_at": None,
            "rejection_reason": None,
            "execution_status": "PENDING",
            "executed_at": None,
            "compensating_transaction_id": None,
            "reconciliation_status": None,
            "reconciliation_details": None,
        }

        details = dict(incident.details or {})
        details["active_proposal"] = proposal_data
        details["investigation_state"] = "ACTION_PROPOSED"
        incident.details = details

        await db.commit()

        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="CORRECTIVE_ACTION_PROPOSED",
            entity_type="CORRECTIVE_ACTION",
            entity_id=action_id,
            metadata={
                "action_id": action_id,
                "incident_id": incident_id,
                "action_type": action_type,
                "proposed_points": req.proposed_points,
                "proposed_by": actor_id,
            },
        )

        return cls._proposal_to_response(incident, proposal_data)

    @classmethod
    async def list_pending_approvals(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> CorrectiveActionListPage:
        # Query incidents that have an active proposal pending approval
        stmt = select(AnomalyIncident).where(AnomalyIncident.status.in_(["DETECTED", "INVESTIGATING"]))
        incidents = (await db.execute(stmt)).scalars().all()

        pending_items: List[CorrectiveActionResponse] = []
        for inc in incidents:
            prop = (inc.details or {}).get("active_proposal")
            if prop and prop.get("approval_status") == "PENDING_APPROVAL":
                pending_items.append(cls._proposal_to_response(inc, prop))

        total_count = len(pending_items)
        offset = (page - 1) * page_size
        paged_items = pending_items[offset : offset + page_size]
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return CorrectiveActionListPage(
            items=paged_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    async def review_proposal(
        cls,
        db: AsyncSession,
        incident_id: str,
        approver_id: str,
        approver_role: str,
        req: ApprovalDecisionRequest,
    ) -> CorrectiveActionResponse:
        """
        Dual-Key Approval / Rejection Engine.
        Enforces two-person control, server-side role validation, rejection reasons,
        and idempotent handling.
        """
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        details = dict(incident.details or {})
        proposal = details.get("active_proposal")
        if not proposal:
            raise NotFoundError(detail=f"No active corrective action proposal found for incident '{incident_id}'.")

        decision = req.decision.upper().strip()
        if decision not in ("APPROVED", "REJECTED"):
            raise BadRequestError(detail=f"Invalid decision '{decision}'. Expected 'APPROVED' or 'REJECTED'.")

        # 1. DUAL-KEY RULE 1: Self-Approval Prevention
        if approver_id == proposal["proposed_by"]:
            raise ForbiddenError(
                detail="Dual-key control violation: You cannot approve your own corrective action proposal. "
                       "A separate authorized reviewer must evaluate this action."
            )

        # 2. DUAL-KEY RULE 2: Role Authorization
        if approver_role not in ("OPERATIONS_MANAGER", "OPERATOR"):
            raise ForbiddenError(detail=f"Role '{approver_role}' lacks authority to approve corrective actions.")

        # 3. DUAL-KEY RULE 3: Idempotent duplicate check
        if proposal.get("execution_status") == "EXECUTED":
            raise ConflictError(detail="This corrective action has already been executed and cannot be re-evaluated.")

        if proposal.get("approval_status") == decision and proposal.get("approver_id") == approver_id:
            # Idempotent response
            return cls._proposal_to_response(incident, proposal)

        # 4. DUAL-KEY RULE 4: Rejection requires mandatory reason
        if decision == "REJECTED":
            if not req.rejection_reason and not req.notes:
                raise BadRequestError(detail="A documented rejection reason is mandatory when rejecting a proposal.")

            rej_reason = req.rejection_reason or req.notes
            now = datetime.now(timezone.utc)

            # Record rejection in corrective_actions table
            action_rec = CorrectiveAction(
                action_id=proposal["action_id"],
                incident_id=incident.incident_id,
                operator_id=approver_id,
                compensating_transaction_id=None,
                decision="REJECTED",
                notes=rej_reason,
                created_at=now,
            )
            db.add(action_rec)

            proposal["approval_status"] = "REJECTED"
            proposal["approver_id"] = approver_id
            proposal["approved_at"] = now.isoformat()
            proposal["rejection_reason"] = rej_reason
            proposal["execution_status"] = "FAILED"
            details["investigation_state"] = "ACTION_REJECTED"
            details["active_proposal"] = proposal
            incident.details = details

            await db.commit()

            await AuditService.log_event(
                db=db,
                actor_id=approver_id,
                action="CORRECTIVE_ACTION_REJECTED",
                entity_type="CORRECTIVE_ACTION",
                entity_id=proposal["action_id"],
                metadata={
                    "action_id": proposal["action_id"],
                    "incident_id": incident.incident_id,
                    "rejection_reason": rej_reason,
                    "rejected_by": approver_id,
                },
            )

            return cls._proposal_to_response(incident, proposal)

        # 5. DUAL-KEY RULE 5: Approved Action Processing
        now = datetime.now(timezone.utc)
        proposal["approval_status"] = "APPROVED"
        proposal["approver_id"] = approver_id
        proposal["approved_at"] = now.isoformat()
        details["investigation_state"] = "ACTION_APPROVED"
        details["active_proposal"] = proposal
        incident.details = details

        # Record approval in corrective_actions table
        action_rec = CorrectiveAction(
            action_id=proposal["action_id"],
            incident_id=incident.incident_id,
            operator_id=approver_id,
            compensating_transaction_id=None,
            decision="APPROVED",
            notes=req.notes or proposal.get("reason"),
            created_at=now,
        )
        db.add(action_rec)
        await db.commit()

        await AuditService.log_event(
            db=db,
            actor_id=approver_id,
            action="CORRECTIVE_ACTION_APPROVED",
            entity_type="CORRECTIVE_ACTION",
            entity_id=proposal["action_id"],
            metadata={
                "action_id": proposal["action_id"],
                "incident_id": incident.incident_id,
                "approved_by": approver_id,
                "action_type": proposal["action_type"],
            },
        )

        # 6. Execute immediately if requested
        if req.execute_immediately:
            return await cls.execute_approved_action(db, incident_id, approver_id)

        return cls._proposal_to_response(incident, proposal)

    @classmethod
    async def execute_approved_action(
        cls,
        db: AsyncSession,
        incident_id: str,
        actor_id: str,
    ) -> CorrectiveActionResponse:
        """
        Executes an approved corrective action safely on the append-only ledger.
        Atomic balance update, compensating transaction, post-reconciliation check,
        and forensic audit event.
        """
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")

        details = dict(incident.details or {})
        proposal = details.get("active_proposal")
        if not proposal:
            raise NotFoundError(detail="No active corrective action proposal found.")

        if proposal.get("approval_status") != "APPROVED":
            raise ConflictError(detail="Cannot execute corrective action: proposal has not been approved.")

        if proposal.get("execution_status") == "EXECUTED":
            # Idempotent response
            return cls._proposal_to_response(incident, proposal)

        action_type = proposal["action_type"]
        account_id = proposal.get("account_id")
        action_id = proposal["action_id"]
        points = proposal.get("proposed_points", 0)
        now = datetime.now(timezone.utc)

        compensating_tx_id = None
        reconciliation_status = None
        reconciliation_details = None

        # 1. Lock loyalty account for safe update
        account = None
        if account_id:
            acc_stmt = select(LoyaltyAccount).where(LoyaltyAccount.account_id == account_id).with_for_update()
            account = (await db.execute(acc_stmt)).scalar_one_or_none()
            if not account and action_type != "DISMISS_FINDING":
                raise NotFoundError(detail=f"Loyalty account '{account_id}' not found.")

        # 2. Execute by Action Type
        if action_type == "ADJUSTMENT_CREDIT":
            compensating_tx_id = f"PTS-ADJ-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            prev_balance = account.current_balance
            new_balance = prev_balance + points

            # Append-only transaction
            comp_tx = PointsTransaction(
                transaction_id=compensating_tx_id,
                account_id=account.account_id,
                order_id=None,
                related_transaction_id=None,
                rule_id=None,
                entry_type="ADJUSTMENT_CREDIT",
                points=points,
                running_balance=new_balance,
                idempotency_key=f"IDEM-REM-CR-{action_id}",
                notes=f"Compensating remediation for incident {incident_id}: {proposal.get('reason')}",
                created_at=now,
            )
            db.add(comp_tx)

            # Create corresponding active points lot so credited points can be redeemed
            comp_lot = PointsLot(
                lot_id=f"LOT-ADJ-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                transaction_id=compensating_tx_id,
                account_id=account.account_id,
                initial_points=points,
                remaining_points=points,
                status="ACTIVE",
                expires_at=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
            )
            db.add(comp_lot)

            # Atomic balance update
            account.current_balance = new_balance
            account.lifetime_accrued += points

        elif action_type == "ADJUSTMENT_DEBIT":
            compensating_tx_id = f"PTS-ADJ-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            prev_balance = account.current_balance
            new_balance = prev_balance - points

            comp_tx = PointsTransaction(
                transaction_id=compensating_tx_id,
                account_id=account.account_id,
                order_id=None,
                related_transaction_id=None,
                rule_id=None,
                entry_type="ADJUSTMENT_DEBIT",
                points=-points,
                running_balance=new_balance,
                idempotency_key=f"IDEM-REM-DB-{action_id}",
                notes=f"Compensating remediation for incident {incident_id}: {proposal.get('reason')}",
                created_at=now,
            )
            db.add(comp_tx)

            # Atomic balance update
            account.current_balance = new_balance

        elif action_type == "ACCOUNT_FREEZE":
            account.status = "FROZEN"

        elif action_type == "ACCOUNT_UNFREEZE":
            account.status = "ACTIVE"

        elif action_type == "DISMISS_FINDING":
            incident.status = "DISMISSED"
            incident.resolved_at = now

        # 3. Link compensating transaction to CorrectiveAction record
        corr_stmt = select(CorrectiveAction).where(CorrectiveAction.action_id == action_id)
        corr_act = (await db.execute(corr_stmt)).scalar_one_or_none()
        if corr_act and compensating_tx_id:
            corr_act.compensating_transaction_id = compensating_tx_id

        # 4. POST-REMEDIATION RECONCILIATION VERIFICATION
        if account_id and action_type in ("ADJUSTMENT_CREDIT", "ADJUSTMENT_DEBIT"):
            # Compute current ledger balance
            sum_stmt = select(func.coalesce(func.sum(PointsTransaction.points), 0)).where(
                PointsTransaction.account_id == account_id
            )
            # Include newly added transaction in calculation
            ledger_sum = (await db.execute(sum_stmt)).scalar() or 0
            # If the session has uncommitted tx, sum_stmt inside transaction reflects flushed balance
            stored_bal = account.current_balance
            drift = stored_bal - ledger_sum

            is_reconciled = (drift == 0)
            reconciliation_status = "RECONCILED" if is_reconciled else "DISCREPANCY_PERSISTS"
            reconciliation_details = {
                "stored_balance": stored_bal,
                "calculated_ledger_balance": ledger_sum,
                "discrepancy": drift,
                "is_reconciled": is_reconciled,
            }

            if is_reconciled:
                incident.status = "RESOLVED"
                incident.resolved_at = now
                details["investigation_state"] = "RECONCILIATION_VERIFIED"
            else:
                incident.status = "INVESTIGATING"
                details["investigation_state"] = "ACTION_EXECUTED_DISCREPANCY_PERSISTS"
                details["remaining_discrepancy"] = drift
        elif action_type in ("ACCOUNT_FREEZE", "ACCOUNT_UNFREEZE"):
            reconciliation_status = "POLICY_ENFORCED"
            details["investigation_state"] = "ACCOUNT_STATUS_UPDATED"
        elif action_type == "DISMISS_FINDING":
            reconciliation_status = "DISMISSED"
            details["investigation_state"] = "FINDING_DISMISSED"

        # Update proposal state
        proposal["execution_status"] = "EXECUTED"
        proposal["executed_at"] = now.isoformat()
        proposal["compensating_transaction_id"] = compensating_tx_id
        proposal["reconciliation_status"] = reconciliation_status
        proposal["reconciliation_details"] = reconciliation_details
        details["active_proposal"] = proposal
        incident.details = details

        await db.commit()

        # Audit event
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="CORRECTIVE_ACTION_EXECUTED",
            entity_type="CORRECTIVE_ACTION",
            entity_id=action_id,
            metadata={
                "action_id": action_id,
                "incident_id": incident_id,
                "action_type": action_type,
                "compensating_transaction_id": compensating_tx_id,
                "reconciliation_status": reconciliation_status,
                "incident_status": incident.status,
            },
        )

        return cls._proposal_to_response(incident, proposal)
