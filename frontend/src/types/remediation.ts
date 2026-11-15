/**
 * LoyaltyOS — Remediation & Dual-Key Approval Engine Types
 * Phase 6 Response Contracts for Frontend Consumption
 */

export type CorrectiveActionType = 
  | 'ADJUSTMENT_CREDIT'
  | 'ADJUSTMENT_DEBIT'
  | 'REVERSAL_REVIEW'
  | 'ACCOUNT_FREEZE'
  | 'ACCOUNT_UNFREEZE'
  | 'DISMISS_FINDING';

export type ApprovalDecision = 'APPROVED' | 'REJECTED';

export type ActionApprovalStatus = 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED';

export type ActionExecutionStatus = 'PENDING' | 'EXECUTED' | 'FAILED';

export interface CorrectiveAction {
  action_id: string;
  incident_id: string;
  account_id?: string;
  customer_id?: string;
  action_type: CorrectiveActionType | string;
  proposed_points: number;
  proposed_by: string;
  proposed_at: string;
  approval_status: ActionApprovalStatus | string;
  status?: string;
  approver_id?: string | null;
  reviewed_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  execution_status: ActionExecutionStatus | string;
  executed_at?: string | null;
  compensating_transaction_id?: string | null;
  execution_tx_id?: string | null;
  reconciliation_status?: string | null;
  reconciliation_details?: Record<string, any> | null;
  notes?: string | null;
  reason?: string | null;
}

export interface CorrectiveActionListPage {
  items: CorrectiveAction[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface InvestigationNote {
  author: string;
  timestamp?: string;
  created_at?: string;
  note: string;
  type?: string;
}

export interface InvestigationDetail {
  incident_id: string;
  issue_type: string;
  entity_type: string;
  entity_id: string;
  variance_amount: string | number;
  status: string;
  investigator_id?: string | null;
  investigation_state: string;
  notes_history: InvestigationNote[];
  notes?: InvestigationNote[];
  active_proposal?: CorrectiveAction | null;
  incident_details: Record<string, any>;
  incident?: any;
  created_at: string;
  resolved_at?: string | null;
}
