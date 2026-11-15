from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class InvestigationOpenRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigator_id: Optional[str] = Field(None, description="Optional investigator user ID (defaults to current user)")
    notes: Optional[str] = Field(None, description="Initial investigation notes")


class InvestigationNoteRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note: str = Field(..., min_length=3, description="Forensic investigation observation or note")


class CorrectiveActionProposalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_type: str = Field(
        ...,
        description="One of: ADJUSTMENT_CREDIT, ADJUSTMENT_DEBIT, REVERSAL_REVIEW, ACCOUNT_FREEZE, ACCOUNT_UNFREEZE, DISMISS_FINDING"
    )
    proposed_points: Optional[int] = Field(0, ge=0, description="Points adjustment for credit/debit actions")
    reason: str = Field(..., min_length=5, description="Business rationale for the proposed corrective action")
    evidence_references: Optional[Dict[str, Any]] = Field(None, description="Supporting transaction or record keys")


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    notes: Optional[str] = Field(None, description="Approval notes")
    rejection_reason: Optional[str] = Field(None, description="Mandatory reason if decision is REJECTED")
    execute_immediately: bool = Field(True, description="Whether to execute the compensating transaction upon approval")


class CorrectiveActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    incident_id: str
    account_id: Optional[str] = None
    customer_id: Optional[str] = None
    action_type: str
    proposed_points: int = 0
    proposed_by: str
    proposed_at: datetime
    approval_status: str  # PENDING_APPROVAL, APPROVED, REJECTED
    approver_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    execution_status: str  # PENDING, EXECUTED, FAILED
    executed_at: Optional[datetime] = None
    compensating_transaction_id: Optional[str] = None
    reconciliation_status: Optional[str] = None
    reconciliation_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CorrectiveActionListPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[CorrectiveActionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class InvestigationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    issue_type: str
    entity_type: str
    entity_id: str
    variance_amount: Decimal
    status: str
    investigator_id: Optional[str] = None
    investigation_state: str
    notes_history: List[Dict[str, Any]] = []
    active_proposal: Optional[CorrectiveActionResponse] = None
    incident_details: Dict[str, Any] = {}
    created_at: datetime
    resolved_at: Optional[datetime] = None
