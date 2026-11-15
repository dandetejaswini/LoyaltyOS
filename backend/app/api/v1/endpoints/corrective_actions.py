from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_role
from backend.app.models.identity import AppUser
from backend.app.models.audit import AnomalyIncident, CorrectiveAction
from backend.app.schemas.intelligence import AnomalyDetailResponse
from backend.app.schemas.remediation import (
    InvestigationOpenRequest,
    InvestigationNoteRequest,
    CorrectiveActionProposalRequest,
    ApprovalDecisionRequest,
    CorrectiveActionResponse,
    CorrectiveActionListPage,
    InvestigationDetailResponse,
)
from backend.app.services.remediation_service import RemediationService
from backend.app.services.intelligence.engine import IntelligenceEngine

router = APIRouter(prefix="/corrective-actions", tags=["Remediation & Dual-Key Approval Engine"])

# Permitted roles for investigation and remediation operations
require_operator_or_manager = require_role(["OPERATOR", "OPERATIONS_MANAGER"])
require_manager_only = require_role(["OPERATIONS_MANAGER"])
require_investigation_team = require_role(["ANALYST", "OPERATOR", "OPERATIONS_MANAGER"])


@router.get("/findings-awaiting-investigation", response_model=List[AnomalyDetailResponse])
async def list_findings_awaiting_investigation(
    status: Optional[str] = Query(None, description="Optional status filter: DETECTED or INVESTIGATING"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AppUser = Depends(require_investigation_team),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists anomaly incidents detected by LLIRE awaiting operator triage or active investigation.
    """
    incidents = await RemediationService.list_awaiting_investigation(
        db=db,
        status=status,
        page=page,
        page_size=page_size,
    )
    return [IntelligenceEngine._finding_to_response(inc) for inc in incidents]


@router.get("/investigations/{incident_id}", response_model=InvestigationDetailResponse)
async def get_investigation_detail(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    current_user: AppUser = Depends(require_investigation_team),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full investigation state, forensic evidence, notes history, and active proposal.
    """
    return await RemediationService.get_investigation_detail(db, incident_id)


@router.post("/investigations/{incident_id}/start", response_model=InvestigationDetailResponse)
async def start_investigation(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    payload: Optional[InvestigationOpenRequest] = None,
    current_user: AppUser = Depends(require_investigation_team),
    db: AsyncSession = Depends(get_db),
):
    """
    Opens an active investigation on a detected anomaly, assigning an investigator
    and recording initial forensic observations. Transitions status to INVESTIGATING.
    """
    investigator_id = payload.investigator_id if payload else None
    notes = payload.notes if payload else None

    return await RemediationService.open_investigation(
        db=db,
        incident_id=incident_id,
        actor_id=str(current_user.id),
        investigator_id=investigator_id,
        notes=notes,
    )


@router.post("/investigations/{incident_id}/notes", response_model=InvestigationDetailResponse)
async def add_investigation_note(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    payload: InvestigationNoteRequest = ...,
    current_user: AppUser = Depends(require_investigation_team),
    db: AsyncSession = Depends(get_db),
):
    """
    Appends forensic notes and observation timestamps to the investigation history.
    """
    return await RemediationService.add_investigation_note(
        db=db,
        incident_id=incident_id,
        actor_id=str(current_user.id),
        note_text=payload.note,
    )


@router.post("/investigations/{incident_id}/propose", response_model=CorrectiveActionResponse)
async def propose_corrective_action(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    payload: CorrectiveActionProposalRequest = ...,
    current_user: AppUser = Depends(require_operator_or_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Proposes a corrective action (ADJUSTMENT_CREDIT, ADJUSTMENT_DEBIT, ACCOUNT_FREEZE, etc.).
    Requires dual-key approval by a second authorized Operations Manager prior to execution.
    """
    return await RemediationService.propose_corrective_action(
        db=db,
        incident_id=incident_id,
        actor_id=str(current_user.id),
        req=payload,
    )


@router.get("/pending-approvals", response_model=CorrectiveActionListPage)
async def list_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AppUser = Depends(require_operator_or_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists all corrective action proposals awaiting dual-key review.
    """
    return await RemediationService.list_pending_approvals(db, page=page, page_size=page_size)


@router.post("/investigations/{incident_id}/review", response_model=CorrectiveActionResponse)
async def review_proposal(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    payload: ApprovalDecisionRequest = ...,
    current_user: AppUser = Depends(require_operator_or_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Dual-Key Approval or Rejection Endpoint.
    Strictly forbids self-approval (proposer != approver).
    Rejection mandates a documented reason.
    Approved actions optionally execute compensating transactions immediately.
    """
    return await RemediationService.review_proposal(
        db=db,
        incident_id=incident_id,
        approver_id=str(current_user.id),
        approver_role=current_user.role,
        req=payload,
    )


@router.post("/investigations/{incident_id}/execute", response_model=CorrectiveActionResponse)
async def execute_approved_correction(
    incident_id: str = Path(..., description="Unique anomaly incident ID"),
    current_user: AppUser = Depends(require_operator_or_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes an approved corrective action on the append-only ledger.
    Applies compensating transaction, locks account, performs post-reconciliation check,
    and updates incident status to RESOLVED only if ledger reconciles.
    """
    return await RemediationService.execute_approved_action(
        db=db,
        incident_id=incident_id,
        actor_id=str(current_user.id),
    )


@router.get("/history", response_model=CorrectiveActionListPage)
async def list_corrective_action_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AppUser = Depends(require_operator_or_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves historical corrective action decisions (APPROVED/REJECTED/EXECUTED)
    from the corrective_actions audit table.
    """
    query = select(CorrectiveAction).order_by(desc(CorrectiveAction.created_at))
    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    records = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()

    items = [
        CorrectiveActionResponse(
            action_id=r.action_id,
            incident_id=r.incident_id,
            action_type="CORRECTIVE_DECISION",
            proposed_points=0,
            proposed_by="SYSTEM",
            proposed_at=r.created_at,
            approval_status=r.decision,
            approver_id=r.operator_id,
            approved_at=r.created_at if r.decision == "APPROVED" else None,
            rejection_reason=r.notes if r.decision == "REJECTED" else None,
            execution_status="EXECUTED" if r.compensating_transaction_id else "RECORDED",
            executed_at=r.created_at if r.compensating_transaction_id else None,
            compensating_transaction_id=r.compensating_transaction_id,
            notes=r.notes,
        )
        for r in records
    ]

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    return CorrectiveActionListPage(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
