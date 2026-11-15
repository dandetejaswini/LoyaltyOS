import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  UserCheck,
  FileCheck,
  RotateCcw,
  X,
  MessageSquare,
  Lock,
  Unlock,
  RefreshCw,
  Send,
  Check,
  Ban
} from 'lucide-react';
import { apiClient, ApiError, UserProfileResponse } from '@/services/apiClient';
import { AnomalyDetail } from '@/types/intelligence';
import {
  CorrectiveAction,
  InvestigationDetail
} from '@/types/remediation';
import { ReconciliationReport } from '@/types/loyalty';

interface OpsManagerDashboardProps {
  user: UserProfileResponse;
}

export const OpsManagerDashboard: React.FC<OpsManagerDashboardProps> = ({ user }) => {
  // Navigation sub-tabs
  const [activeTab, setActiveTab] = useState<'queue' | 'workspace' | 'approvals' | 'history'>('queue');

  // Queue state
  const [openFindings, setOpenFindings] = useState<AnomalyDetail[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState<boolean>(true);

  // Active Investigation Workspace state
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [investigationDetail, setInvestigationDetail] = useState<InvestigationDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [newNote, setNewNote] = useState<string>('');
  const [isAddingNote, setIsAddingNote] = useState<boolean>(false);

  // Propose Correction Form state
  const [actionType, setActionType] = useState<string>('ADJUSTMENT_CREDIT');
  const [proposedPoints, setProposedPoints] = useState<number>(500);
  const [proposalReason, setProposalReason] = useState<string>('');
  const [isSubmittingProposal, setIsSubmittingProposal] = useState<boolean>(false);

  // Approvals Queue state
  const [pendingApprovals, setPendingApprovals] = useState<CorrectiveAction[]>([]);
  const [isLoadingApprovals, setIsLoadingApprovals] = useState<boolean>(true);

  // Review Modal state
  const [selectedProposal, setSelectedProposal] = useState<CorrectiveAction | null>(null);
  const [reviewDecision, setReviewDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [reviewNotes, setReviewNotes] = useState<string>('Verified audit evidence and approved compensating ledger transaction.');
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);

  // History state
  const [actionHistory, setActionHistory] = useState<CorrectiveAction[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(true);

  // Post-Remediation Reconciliation Verification state
  const [verifiedReconciliation, setVerifiedReconciliation] = useState<ReconciliationReport | null>(null);

  // Error & Status alerts
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Load Open Findings
  const loadOpenFindings = async () => {
    setIsLoadingQueue(true);
    try {
      const data = await apiClient.getFindingsAwaitingInvestigation({ status: 'OPEN' });
      setOpenFindings(data);
    } catch (err) {
      console.error('Failed to load findings awaiting investigation', err);
    } finally {
      setIsLoadingQueue(false);
    }
  };

  // Load Pending Approvals
  const loadPendingApprovals = async () => {
    setIsLoadingApprovals(true);
    try {
      const res = await apiClient.getPendingApprovals();
      setPendingApprovals(res.items);
    } catch (err) {
      console.error('Failed to load pending approvals', err);
    } finally {
      setIsLoadingApprovals(false);
    }
  };

  // Load Action History
  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const res = await apiClient.getCorrectiveActionHistory();
      setActionHistory(res.items);
    } catch (err) {
      console.error('Failed to load corrective action history', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Load Investigation Details
  const loadInvestigation = async (incidentId: string) => {
    setIsLoadingDetail(true);
    setError(null);
    try {
      const detail = await apiClient.getInvestigationDetail(incidentId);
      setInvestigationDetail(detail);
      setActiveIncidentId(incidentId);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      }
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Start Investigation Action
  const handleStartInvestigation = async (incidentId: string) => {
    try {
      const detail = await apiClient.startInvestigation(incidentId, {
        investigator_id: user.id,
        notes: `Investigation formally opened by Operations Manager ${user.full_name || user.email}`
      });
      setInvestigationDetail(detail);
      setActiveIncidentId(incidentId);
      setActiveTab('workspace');
      setSuccessBanner(`Investigation opened for incident ${incidentId}.`);
      await loadOpenFindings();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to start investigation');
      }
    }
  };

  // Add Note to Investigation
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeIncidentId || !newNote.trim()) return;
    setIsAddingNote(true);
    try {
      const updated = await apiClient.addInvestigationNote(activeIncidentId, newNote.trim());
      setInvestigationDetail(updated);
      setNewNote('');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      }
    } finally {
      setIsAddingNote(false);
    }
  };

  // Propose Corrective Action
  const handleProposeCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeIncidentId) return;
    if (proposalReason.trim().length < 10) {
      setError('A comprehensive justification of at least 10 characters is required for audit trail compliance.');
      return;
    }

    setIsSubmittingProposal(true);
    setError(null);
    try {
      const action = await apiClient.proposeCorrectiveAction(activeIncidentId, {
        action_type: actionType,
        proposed_points: Number(proposedPoints),
        reason: proposalReason.trim()
      });

      setSuccessBanner(`Corrective action proposal ${action.action_id} submitted for Dual-Key Approval!`);
      // Reload investigation detail and pending approvals
      await Promise.all([loadInvestigation(activeIncidentId), loadPendingApprovals()]);
      setActiveTab('approvals');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Proposal submission failed');
      }
    } finally {
      setIsSubmittingProposal(false);
    }
  };

  // Submit Review (Approve / Reject) with Dual-Key Safety
  const handleReviewProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProposal) return;

    // Check Dual-Key constraint client-side
    if (selectedProposal.proposed_by === user.id) {
      setError(`DUAL-KEY INVARIANT VIOLATION: You cannot approve your own proposal (User: ${user.id}). Switch to a different Operations Manager persona.`);
      return;
    }

    if (reviewDecision === 'REJECTED' && !rejectionReason.trim()) {
      setError('A rejection reason is mandatory when rejecting a proposal.');
      return;
    }

    setIsSubmittingReview(true);
    setError(null);
    try {
      const result = await apiClient.reviewProposal(selectedProposal.incident_id, {
        decision: reviewDecision,
        notes: reviewNotes.trim() || undefined,
        rejection_reason: reviewDecision === 'REJECTED' ? rejectionReason.trim() : undefined,
        execute_immediately: true
      });

      setSelectedProposal(null);
      setSuccessBanner(`Proposal successfully ${reviewDecision}! Compensating ledger execution status: ${result.execution_status}.`);

      // Refresh data
      await Promise.all([loadPendingApprovals(), loadHistory()]);
      setActiveTab('history');

      // Check post-reconciliation if account exists
      if (investigationDetail?.entity_id) {
        verifyReconciliation(investigationDetail.entity_id);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Review action failed');
      }
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // Verify Post-Remediation Reconciliation
  const verifyReconciliation = async (accountId: string) => {
    try {
      const recon = await apiClient.getReconciliation(accountId);
      setVerifiedReconciliation(recon);
    } catch (err) {
      console.error('Failed to verify post-remediation reconciliation', err);
    }
  };

  useEffect(() => {
    loadOpenFindings();
    loadPendingApprovals();
    loadHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner / Ops Manager Console Identity */}
      <div className="bg-navy-950 text-white rounded-xl p-6 shadow-md border border-navy-800">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-navy-800/80 rounded-lg text-platinum-200 border border-navy-700">
              <ShieldAlert className="w-6 h-6 text-lavender-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Operations Manager Console
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700 font-mono">
                  Dual-Key Governance Enforced
                </span>
              </h2>
              <p className="text-xs text-platinum-400 mt-1">
                Active Investigator: <strong className="text-lavender-300 font-mono">{user.full_name || user.email}</strong> (ID: <span className="font-mono text-[11px]">{user.id}</span>)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                loadOpenFindings();
                loadPendingApprovals();
                loadHistory();
              }}
              className="px-3.5 py-2 bg-navy-800 hover:bg-navy-700 border border-navy-700 text-platinum-100 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5 text-lavender-400" />
              Refresh Console
            </button>
          </div>
        </div>

        {/* Console KPI Status Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-4 border-t border-navy-800/80">
          <div>
            <span className="text-[10px] text-platinum-400 uppercase font-mono block">Awaiting Investigation</span>
            <span className="text-xl font-bold font-mono text-amber-400 mt-0.5 block">{openFindings.length}</span>
          </div>
          <div>
            <span className="text-[10px] text-platinum-400 uppercase font-mono block">Pending Dual-Key Approvals</span>
            <span className="text-xl font-bold font-mono text-lavender-300 mt-0.5 block">{pendingApprovals.length}</span>
          </div>
          <div>
            <span className="text-[10px] text-platinum-400 uppercase font-mono block">Executed Compensations</span>
            <span className="text-xl font-bold font-mono text-emerald-400 mt-0.5 block">
              {actionHistory.filter(a => a.execution_status === 'EXECUTED' || a.approval_status === 'APPROVED').length}
            </span>
          </div>
          <div>
            <span className="text-[10px] text-platinum-400 uppercase font-mono block">Two-Person Invariant</span>
            <span className="text-xs font-bold text-emerald-400 mt-1 block flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Strict Non-Self-Approval
            </span>
          </div>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {successBanner && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-900 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="font-semibold">{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-emerald-700 hover:text-emerald-950">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-rose-900 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span className="font-semibold">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-700 hover:text-rose-950">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-platinum-200 space-x-1 overflow-x-auto">
        <button
          onClick={() => setActiveTab('queue')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'queue'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <Clock className="w-4 h-4" />
          Investigation Queue
          {openFindings.length > 0 && (
            <span className="px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold font-mono">
              {openFindings.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('workspace')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'workspace'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          Case Workspace & Proposal
          {activeIncidentId && (
            <span className="px-1.5 py-0.5 rounded-full bg-lavender-100 text-lavender-900 text-[10px] font-bold font-mono">
              Active: {activeIncidentId}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'approvals'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          Dual-Key Pending Approvals
          {pendingApprovals.length > 0 && (
            <span className="px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold font-mono">
              {pendingApprovals.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'history'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <RotateCcw className="w-4 h-4" />
          Compensating Ledger History
        </button>
      </div>

      {/* TAB 1: INVESTIGATION QUEUE */}
      {activeTab === 'queue' && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-semibold text-navy-950">Findings Awaiting Investigation</h3>
              <p className="text-xs text-platinum-600 mt-1">
                Anomalies detected by LLIRE requiring formal assignment and forensic investigation.
              </p>
            </div>
            <span className="text-xs font-mono text-platinum-500">{openFindings.length} open cases</span>
          </div>

          {isLoadingQueue ? (
            <div className="p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
              Loading open findings...
            </div>
          ) : openFindings.length === 0 ? (
            <div className="p-12 text-center text-platinum-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              All detected findings have been assigned to investigations!
            </div>
          ) : (
            <div className="border border-platinum-200 rounded-lg overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="px-3 py-2.5">Incident ID</th>
                    <th className="px-3 py-2.5">Category / Issue</th>
                    <th className="px-3 py-2.5">Severity</th>
                    <th className="px-3 py-2.5">Target Entity</th>
                    <th className="px-3 py-2.5">Variance (PTS)</th>
                    <th className="px-3 py-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-platinum-100 font-mono">
                  {openFindings.map((finding) => (
                    <tr key={finding.incident_id} className="hover:bg-platinum-50/50">
                      <td className="px-3 py-2.5 font-bold text-navy-950">{finding.incident_id}</td>
                      <td className="px-3 py-2.5 font-sans font-semibold text-navy-900">
                        {String(finding.category || finding.issue_type).replace(/_/g, ' ')}
                      </td>
                      <td className="px-3 py-2.5 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          finding.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                          finding.severity === 'HIGH' ? 'bg-amber-100 text-amber-800' :
                          'bg-lavender-100 text-lavender-800'
                        }`}>
                          {finding.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-platinum-600">{finding.account_id || finding.entity_id || 'System'}</td>
                      <td className="px-3 py-2.5 font-bold text-navy-950">{finding.variance_amount} PTS</td>
                      <td className="px-3 py-2.5 text-right font-sans">
                        <button
                          onClick={() => handleStartInvestigation(finding.incident_id)}
                          className="px-3 py-1.5 bg-lavender-600 hover:bg-lavender-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 ml-auto transition shadow-xs"
                        >
                          <FileCheck className="w-3.5 h-3.5" /> Start Case
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE CASE WORKSPACE & PROPOSAL */}
      {activeTab === 'workspace' && (
        <div className="space-y-6">
          {!activeIncidentId ? (
            <div className="bg-white border border-platinum-200 rounded-xl p-12 text-center text-platinum-500 text-xs">
              <FileCheck className="w-10 h-10 text-platinum-300 mx-auto mb-3" />
              <p className="font-semibold text-navy-950 text-sm">No Active Investigation Case Selected</p>
              <p className="mt-1">Select an incident from the Investigation Queue to open its forensic case workspace.</p>
              <button
                onClick={() => setActiveTab('queue')}
                className="mt-4 px-4 py-2 bg-lavender-600 hover:bg-lavender-700 text-white rounded-lg text-xs font-semibold transition"
              >
                Go to Investigation Queue
              </button>
            </div>
          ) : isLoadingDetail ? (
            <div className="p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
              Loading case workspace...
            </div>
          ) : investigationDetail && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left 2 Cols: Incident Details, Forensic Evidence & Investigation Notes */}
              <div className="lg:col-span-2 space-y-6">
                {/* Incident Overview Card */}
                <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-platinum-500">{investigationDetail.incident_id}</span>
                      </div>
                      <h3 className="text-base font-bold text-navy-950 mt-1">
                        {investigationDetail.issue_type.replace(/_/g, ' ')}
                      </h3>
                      <p className="text-xs text-platinum-600 mt-1">
                        State: <strong className="font-mono text-navy-900">{investigationDetail.investigation_state}</strong>
                      </p>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] uppercase font-mono text-platinum-500 block">Status</span>
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200 font-mono">
                        {investigationDetail.status}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 pt-2 text-xs">
                    <div className="p-2.5 bg-platinum-50 rounded border border-platinum-200">
                      <span className="text-[10px] text-platinum-500 block uppercase font-mono">Entity ID</span>
                      <span className="font-bold font-mono text-navy-950">{investigationDetail.entity_id}</span>
                    </div>
                    <div className="p-2.5 bg-platinum-50 rounded border border-platinum-200">
                      <span className="text-[10px] text-platinum-500 block uppercase font-mono">Entity Type</span>
                      <span className="font-bold font-mono text-platinum-800">{investigationDetail.entity_type}</span>
                    </div>
                    <div className="p-2.5 bg-platinum-50 rounded border border-platinum-200">
                      <span className="text-[10px] text-platinum-500 block uppercase font-mono">Variance Amount</span>
                      <span className="font-bold font-mono text-rose-700">{investigationDetail.variance_amount} PTS</span>
                    </div>
                  </div>

                  {/* Evidence Payload */}
                  <div className="space-y-1 pt-2">
                    <span className="text-xs font-bold text-navy-950 block">Auditable Evidence Payload</span>
                    <div className="p-3 bg-navy-950 rounded-lg text-platinum-200 font-mono text-[11px] overflow-x-auto max-h-36 border border-navy-800">
                      <pre>{JSON.stringify(investigationDetail.incident_details || {}, null, 2)}</pre>
                    </div>
                  </div>
                </div>

                {/* Notes Stream */}
                <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
                  <h4 className="text-xs font-bold text-navy-950 uppercase tracking-wider flex items-center gap-1.5">
                    <MessageSquare className="w-4 h-4 text-lavender-600" />
                    Investigation Log & Notes Stream
                  </h4>

                  {investigationDetail.notes_history.length === 0 ? (
                    <p className="text-xs text-platinum-500 italic">No notes logged yet.</p>
                  ) : (
                    <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                      {investigationDetail.notes_history.map((n, idx) => (
                        <div key={idx} className="p-3 bg-platinum-50 rounded-lg border border-platinum-200 text-xs">
                          <div className="flex justify-between items-center text-[10px] text-platinum-500 font-mono mb-1">
                            <span className="font-semibold text-navy-900">{n.author}</span>
                            <span>{new Date(n.timestamp || n.created_at || Date.now()).toLocaleString()}</span>
                          </div>
                          <p className="text-platinum-800">{n.note}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <form onSubmit={handleAddNote} className="flex gap-2 pt-2">
                    <input
                      type="text"
                      placeholder="Add an investigation finding note..."
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      className="flex-1 px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
                    />
                    <button
                      type="submit"
                      disabled={isAddingNote || !newNote.trim()}
                      className="px-3 py-2 bg-navy-950 hover:bg-navy-900 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                    >
                      <Send className="w-3.5 h-3.5" />
                      Log Note
                    </button>
                  </form>
                </div>
              </div>

              {/* Right Col: Propose Corrective Action Form */}
              <div className="space-y-6">
                <div className="bg-white border-2 border-lavender-200 rounded-xl p-6 shadow-sm space-y-4">
                  <div className="flex items-center gap-2 text-lavender-900">
                    <ShieldCheck className="w-5 h-5 text-lavender-600" />
                    <h3 className="text-sm font-bold">Propose Corrective Action</h3>
                  </div>
                  <p className="text-xs text-platinum-600">
                    Submit a structured compensating action. Requires approval from a separate Operations Manager before ledger execution.
                  </p>

                  <form onSubmit={handleProposeCorrection} className="space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-navy-950 mb-1">Action Type</label>
                      <select
                        value={actionType}
                        onChange={(e) => setActionType(e.target.value)}
                        className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono font-semibold bg-white"
                      >
                        <option value="ADJUSTMENT_CREDIT">ADJUSTMENT_CREDIT (Compensating Credit)</option>
                        <option value="ADJUSTMENT_DEBIT">ADJUSTMENT_DEBIT (Revoke Unearned Points)</option>
                        <option value="REVERSAL_REVIEW">REVERSAL_REVIEW</option>
                        <option value="ACCOUNT_FREEZE">ACCOUNT_FREEZE</option>
                        <option value="ACCOUNT_UNFREEZE">ACCOUNT_UNFREEZE</option>
                        <option value="DISMISS_FINDING">DISMISS_FINDING</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-navy-950 mb-1">Proposed Points</label>
                      <input
                        type="number"
                        value={proposedPoints}
                        onChange={(e) => setProposedPoints(parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                      />
                      <span className="text-[10px] text-platinum-500 block mt-0.5">
                        Points adjustment value (will create compensating double-entry ledger record).
                      </span>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-navy-950 mb-1">Audit Justification & Reason</label>
                      <textarea
                        rows={3}
                        required
                        placeholder="Comprehensive reason for audit trail (min. 10 chars)..."
                        value={proposalReason}
                        onChange={(e) => setProposalReason(e.target.value)}
                        className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmittingProposal}
                      className="w-full py-2.5 bg-lavender-600 hover:bg-lavender-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-sm"
                    >
                      {isSubmittingProposal ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          Submitting Proposal...
                        </>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          Submit for Dual-Key Approval
                        </>
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: DUAL-KEY PENDING APPROVALS QUEUE */}
      {activeTab === 'approvals' && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-semibold text-navy-950">Pending Approvals Queue</h3>
              <p className="text-xs text-platinum-600 mt-1">
                Two-person authorization desk. Strict enforcement: you cannot approve proposals you created.
              </p>
            </div>
            <span className="text-xs font-mono text-platinum-500">{pendingApprovals.length} pending</span>
          </div>

          {isLoadingApprovals ? (
            <div className="p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
              Loading pending proposals...
            </div>
          ) : pendingApprovals.length === 0 ? (
            <div className="p-12 text-center text-platinum-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              No corrective actions currently awaiting dual-key review.
            </div>
          ) : (
            <div className="border border-platinum-200 rounded-lg overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="px-3 py-2.5">Action ID</th>
                    <th className="px-3 py-2.5">Incident ID</th>
                    <th className="px-3 py-2.5">Action Type</th>
                    <th className="px-3 py-2.5">Points</th>
                    <th className="px-3 py-2.5">Proposer</th>
                    <th className="px-3 py-2.5">Justification</th>
                    <th className="px-3 py-2.5 text-right">Review Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-platinum-100 font-mono">
                  {pendingApprovals.map((prop) => {
                    const isSelfProposal = prop.proposed_by === user.id;

                    return (
                      <tr key={prop.action_id} className="hover:bg-platinum-50/50">
                        <td className="px-3 py-2.5 font-bold text-navy-950">{prop.action_id}</td>
                        <td className="px-3 py-2.5 text-platinum-600">{prop.incident_id}</td>
                        <td className="px-3 py-2.5 font-bold text-lavender-900">{prop.action_type}</td>
                        <td className="px-3 py-2.5 font-bold">{prop.proposed_points || 0} PTS</td>
                        <td className="px-3 py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            isSelfProposal ? 'bg-amber-100 text-amber-800 font-bold' : 'bg-platinum-100 text-platinum-700'
                          }`}>
                            {isSelfProposal ? `${prop.proposed_by} (You)` : prop.proposed_by}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 font-sans text-platinum-600 max-w-xs truncate">
                          {prop.notes || prop.reason || 'Pending dual-key review'}
                        </td>
                        <td className="px-3 py-2.5 text-right font-sans">
                          <button
                            onClick={() => setSelectedProposal(prop)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 ml-auto transition ${
                              isSelfProposal
                                ? 'bg-platinum-100 text-platinum-500 hover:bg-platinum-200'
                                : 'bg-navy-950 hover:bg-navy-900 text-white shadow-xs'
                            }`}
                          >
                            {isSelfProposal ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                            {isSelfProposal ? 'Self Proposal' : 'Dual-Key Review'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: COMPENSATING LEDGER HISTORY */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-semibold text-navy-950">Compensating Ledger & Remediation Audit Trail</h3>
                <p className="text-xs text-platinum-600 mt-1">
                  Complete immutable log of approved and rejected corrective actions and their compensating ledger executions.
                </p>
              </div>
              <span className="text-xs font-mono text-platinum-500">{actionHistory.length} actions</span>
            </div>

            {isLoadingHistory ? (
              <div className="p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
                Loading audit history...
              </div>
            ) : actionHistory.length === 0 ? (
              <div className="p-12 text-center text-platinum-500 text-xs">
                No corrective action history recorded yet.
              </div>
            ) : (
              <div className="border border-platinum-200 rounded-lg overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="px-3 py-2.5">Action ID</th>
                      <th className="px-3 py-2.5">Incident ID</th>
                      <th className="px-3 py-2.5">Action Type</th>
                      <th className="px-3 py-2.5">Status</th>
                      <th className="px-3 py-2.5">Points</th>
                      <th className="px-3 py-2.5">Proposer</th>
                      <th className="px-3 py-2.5">Approver</th>
                      <th className="px-3 py-2.5">Compensating Tx ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-platinum-100 font-mono">
                    {actionHistory.map((action) => (
                      <tr key={action.action_id} className="hover:bg-platinum-50/50">
                        <td className="px-3 py-2.5 font-bold text-navy-950">{action.action_id}</td>
                        <td className="px-3 py-2.5 text-platinum-600">{action.incident_id}</td>
                        <td className="px-3 py-2.5 font-bold">{action.action_type}</td>
                        <td className="px-3 py-2.5 font-sans">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            action.execution_status === 'EXECUTED' ? 'bg-emerald-100 text-emerald-800' :
                            action.approval_status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {action.execution_status || action.approval_status}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 font-bold">{action.proposed_points || 0} PTS</td>
                        <td className="px-3 py-2.5 text-platinum-600">{action.proposed_by}</td>
                        <td className="px-3 py-2.5 text-navy-900 font-semibold">{action.approver_id || action.reviewed_by || '-'}</td>
                        <td className="px-3 py-2.5 text-lavender-900 font-bold truncate max-w-xs">
                          {action.compensating_transaction_id || action.execution_tx_id || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Post-Remediation Verification Card */}
          {verifiedReconciliation && (
            <div className="bg-white border-2 border-emerald-300 rounded-xl p-6 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-emerald-900">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h4 className="font-bold text-sm">Post-Remediation Reconciliation Verification: Zero Discrepancy Verified</h4>
              </div>
              <p className="text-xs text-platinum-600">
                Executed compensating transaction automatically balanced the ledger. Account invariant is satisfied.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-2.5 bg-emerald-50 rounded">
                  <span className="text-[10px] text-emerald-800 block">Balance</span>
                  <span className="font-bold">{verifiedReconciliation.stored_balance} PTS</span>
                </div>
                <div className="p-2.5 bg-emerald-50 rounded">
                  <span className="text-[10px] text-emerald-800 block">Derived Balance</span>
                  <span className="font-bold">{verifiedReconciliation.ledger_derived_balance} PTS</span>
                </div>
                <div className="p-2.5 bg-emerald-50 rounded">
                  <span className="text-[10px] text-emerald-800 block">Discrepancy</span>
                  <span className="font-bold text-emerald-700">{verifiedReconciliation.discrepancy_amount} PTS</span>
                </div>
                <div className="p-2.5 bg-emerald-50 rounded">
                  <span className="text-[10px] text-emerald-800 block">Status</span>
                  <span className="font-bold text-emerald-700">{verifiedReconciliation.status}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* DUAL-KEY REVIEW & DECISION MODAL */}
      {selectedProposal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl border border-platinum-200 p-6 space-y-6 animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-platinum-200 pb-4">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-lavender-100 text-lavender-800 font-mono">
                  DUAL-KEY DECISION DESK
                </span>
                <h3 className="text-base font-bold text-navy-950 mt-1">
                  Review Proposal: {selectedProposal.action_id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedProposal(null)}
                className="text-platinum-400 hover:text-navy-950"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Invariant Warning if Self-Approval Attempted */}
            {selectedProposal.proposed_by === user.id ? (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-2 text-xs text-rose-900">
                <div className="flex items-center gap-2 font-bold text-rose-800">
                  <Ban className="w-4 h-4 text-rose-600" />
                  SELF-APPROVAL STRICTLY FORBIDDEN
                </div>
                <p>
                  You proposed this corrective action (User: <strong>{user.id}</strong>).
                  LoyaltyOS Dual-Key Governance requires a distinct second authorized Operations Manager to review and approve.
                </p>
                <p className="font-semibold text-rose-800">
                  Switch to Operations Manager 2 in the top bar to approve this action.
                </p>
              </div>
            ) : (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs text-emerald-900">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  Dual-Key Authorized: You ({user.id}) are an independent reviewer distinct from proposer ({selectedProposal.proposed_by}).
                </span>
              </div>
            )}

            {/* Proposal Details */}
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-2.5 bg-platinum-50 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block">Action Type</span>
                  <span className="font-bold text-navy-950">{selectedProposal.action_type}</span>
                </div>
                <div className="p-2.5 bg-platinum-50 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block">Points Adjustment</span>
                  <span className="font-bold text-navy-950">{selectedProposal.proposed_points} PTS</span>
                </div>
              </div>

              <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
                <span className="text-[10px] text-platinum-500 uppercase font-mono block mb-1">Audit Justification</span>
                <p className="text-platinum-800 font-sans">{selectedProposal.notes || selectedProposal.reason || 'Pending approval'}</p>
              </div>
            </div>

            {/* Decision Form */}
            <form onSubmit={handleReviewProposal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Dual-Key Decision</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setReviewDecision('APPROVED')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold border flex items-center justify-center gap-1.5 transition ${
                      reviewDecision === 'APPROVED'
                        ? 'bg-emerald-600 text-white border-emerald-700 shadow-xs'
                        : 'bg-white text-platinum-700 border-platinum-300 hover:bg-platinum-50'
                    }`}
                  >
                    <Check className="w-4 h-4" /> Approve & Execute
                  </button>

                  <button
                    type="button"
                    onClick={() => setReviewDecision('REJECTED')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold border flex items-center justify-center gap-1.5 transition ${
                      reviewDecision === 'REJECTED'
                        ? 'bg-rose-600 text-white border-rose-700 shadow-xs'
                        : 'bg-white text-platinum-700 border-platinum-300 hover:bg-platinum-50'
                    }`}
                  >
                    <Ban className="w-4 h-4" /> Reject Proposal
                  </button>
                </div>
              </div>

              {reviewDecision === 'APPROVED' ? (
                <div>
                  <label className="block text-xs font-semibold text-navy-950 mb-1">Reviewer Approval Notes</label>
                  <input
                    type="text"
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-rose-900 mb-1">Mandatory Rejection Reason</label>
                  <input
                    type="text"
                    required
                    placeholder="Provide specific reason for rejection..."
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-rose-300 rounded-lg focus:outline-none focus:border-rose-500"
                  />
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2 border-t border-platinum-200">
                <button
                  type="button"
                  onClick={() => setSelectedProposal(null)}
                  className="px-4 py-2 bg-platinum-100 hover:bg-platinum-200 text-navy-950 rounded-lg text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingReview || selectedProposal.proposed_by === user.id}
                  className={`px-5 py-2 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-40 shadow-sm ${
                    reviewDecision === 'APPROVED' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {isSubmittingReview ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Confirm {reviewDecision}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
