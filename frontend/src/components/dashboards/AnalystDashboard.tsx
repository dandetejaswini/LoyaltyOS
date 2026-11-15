import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Play,
  Award,
  Filter,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Eye,
  X
} from 'lucide-react';
import { apiClient, ApiError, UserProfileResponse } from '@/services/apiClient';
import {
  AnomalyDetail,
  IntelligenceSummary,
  EngineEvaluationResponse,
  DetectionRunResponse
} from '@/types/intelligence';

interface AnalystDashboardProps {
  user: UserProfileResponse;
}

export const AnalystDashboard: React.FC<AnalystDashboardProps> = ({ user: _user }) => {
  // Summary & KPIs
  const [summary, setSummary] = useState<IntelligenceSummary | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState<boolean>(true);

  // Anomalies list
  const [anomalies, setAnomalies] = useState<AnomalyDetail[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [isLoadingAnomalies, setIsLoadingAnomalies] = useState<boolean>(true);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Selected Anomaly for Forensic Explainability Drawer
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyDetail | null>(null);

  // Detection Run state
  const [isRunningDetection, setIsRunningDetection] = useState<boolean>(false);
  const [detectionResult, setDetectionResult] = useState<DetectionRunResponse | null>(null);

  // Evaluation / Benchmark state
  const [isLoadingEvaluation, setIsLoadingEvaluation] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<EngineEvaluationResponse | null>(null);

  // Error handling
  const [error, setError] = useState<string | null>(null);

  // Load KPI Summary
  const loadSummary = async () => {
    setIsLoadingSummary(true);
    try {
      const data = await apiClient.getIntelligenceSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load intelligence summary', err);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  // Load Anomalies Table
  const loadAnomalies = async (page = 1) => {
    setIsLoadingAnomalies(true);
    setError(null);
    try {
      const res = await apiClient.getAnomalies({
        page,
        pageSize: 10,
        category: categoryFilter || undefined,
        severity: severityFilter || undefined,
        status: statusFilter || undefined
      });
      setAnomalies(res.items);
      setTotalCount(res.total_count);
      setCurrentPage(res.page);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load anomalies');
      }
    } finally {
      setIsLoadingAnomalies(false);
    }
  };

  // Trigger Detection Engine
  const handleRunDetection = async () => {
    setIsRunningDetection(true);
    setDetectionResult(null);
    try {
      const result = await apiClient.runDetection();
      setDetectionResult(result);
      // Refresh summary and anomalies list
      await Promise.all([loadSummary(), loadAnomalies(1)]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Detection run failed');
      }
    } finally {
      setIsRunningDetection(false);
    }
  };

  // Run Ground Truth Evaluation Benchmark
  const handleRunEvaluation = async () => {
    setIsLoadingEvaluation(true);
    try {
      const res = await apiClient.getEvaluation();
      setEvaluation(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError(err instanceof Error ? err.message : 'Evaluation benchmark failed');
      }
    } finally {
      setIsLoadingEvaluation(false);
    }
  };

  // Inspect Anomaly Forensic Details
  const handleInspectAnomaly = async (incidentId: string) => {
    try {
      const detail = await apiClient.getAnomalyDetail(incidentId);
      setSelectedAnomaly(detail);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      }
    }
  };

  useEffect(() => {
    loadSummary();
    loadAnomalies(1);
  }, [categoryFilter, severityFilter, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Top Banner / Analyst Hub Header */}
      <div className="bg-navy-950 text-white rounded-xl p-6 shadow-md border border-navy-800">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-navy-800/80 rounded-lg text-platinum-200 border border-navy-700">
              <BarChart3 className="w-6 h-6 text-lavender-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Analyst Hub
                <span className="text-xs px-2 py-0.5 rounded-full bg-lavender-900/60 text-lavender-300 border border-lavender-700">
                  LLIRE Intelligence Engine
                </span>
              </h2>
              <p className="text-xs text-platinum-400 mt-1">
                Auditable fraud & accounting anomaly detection, forensic explainability, and ground-truth benchmark metrics.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={handleRunDetection}
              disabled={isRunningDetection}
              className="px-3.5 py-2 bg-lavender-600 hover:bg-lavender-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
            >
              <Play className={`w-3.5 h-3.5 ${isRunningDetection ? 'animate-spin' : ''}`} />
              {isRunningDetection ? 'Scanning Ledger...' : 'Run LLIRE Detection'}
            </button>

            <button
              onClick={handleRunEvaluation}
              disabled={isLoadingEvaluation}
              className="px-3.5 py-2 bg-navy-800 hover:bg-navy-700 border border-navy-600 disabled:opacity-50 text-platinum-100 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <Award className={`w-3.5 h-3.5 text-lavender-400 ${isLoadingEvaluation ? 'animate-spin' : ''}`} />
              Benchmark Evaluation
            </button>
          </div>
        </div>

        {/* Detection Run Toast Banner */}
        {detectionResult && (
          <div className="mt-4 p-3 bg-navy-900/90 border border-lavender-700/60 rounded-lg flex items-center justify-between text-xs text-platinum-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                LLIRE scan completed. Detected <strong>{detectionResult.total_anomalies_detected} anomalies</strong> across {detectionResult.detectors_run.length} detectors.
                ({detectionResult.new_incidents_created} new, {detectionResult.existing_incidents_skipped} existing)
              </span>
            </div>
            <button
              onClick={() => setDetectionResult(null)}
              className="text-platinum-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between gap-3 text-rose-800 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">Total Incidents</span>
          <span className="text-2xl font-bold font-mono text-navy-950 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.total_incidents ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">All detected flags</span>
        </div>

        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">Open Findings</span>
          <span className="text-2xl font-bold font-mono text-amber-600 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.open_incidents ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">Awaiting investigation</span>
        </div>

        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">Critical Severity</span>
          <span className="text-2xl font-bold font-mono text-rose-600 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.by_severity?.CRITICAL ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">Highest priority</span>
        </div>

        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">High Severity</span>
          <span className="text-2xl font-bold font-mono text-amber-700 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.by_severity?.HIGH ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">Material risk</span>
        </div>

        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">Investigating</span>
          <span className="text-2xl font-bold font-mono text-lavender-900 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.investigating_incidents ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">In flight review</span>
        </div>

        <div className="p-4 bg-white rounded-xl border border-platinum-200 shadow-sm">
          <span className="text-[11px] text-platinum-500 uppercase tracking-wider block font-mono">Resolved</span>
          <span className="text-2xl font-bold font-mono text-emerald-700 mt-1 block">
            {isLoadingSummary ? '...' : (summary?.resolved_incidents ?? 0)}
          </span>
          <span className="text-[10px] text-platinum-400 block mt-1">Compensated & closed</span>
        </div>
      </div>

      {/* Benchmark Evaluation Modal/Banner */}
      {evaluation && (
        <div className="bg-white border-2 border-lavender-300 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-lavender-600" />
              <h3 className="text-base font-bold text-navy-950">
                Ground-Truth Benchmark Evaluation Results
              </h3>
            </div>
            <button onClick={() => setEvaluation(null)} className="text-platinum-400 hover:text-navy-950">
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-platinum-600">
            Measured against deterministic synthetic anomalies seeded in Phase 3. Confirms detection accuracy across all standard detectors.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-center">
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[10px] font-mono text-platinum-500 uppercase block">True Positives</span>
              <span className="text-xl font-bold font-mono text-emerald-700">{evaluation.aggregate.true_positives}</span>
            </div>
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[10px] font-mono text-platinum-500 uppercase block">False Positives</span>
              <span className="text-xl font-bold font-mono text-navy-950">{evaluation.aggregate.false_positives}</span>
            </div>
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[10px] font-mono text-platinum-500 uppercase block">False Negatives</span>
              <span className="text-xl font-bold font-mono text-navy-950">{evaluation.aggregate.false_negatives}</span>
            </div>
            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <span className="text-[10px] font-mono text-emerald-800 uppercase block font-semibold">Precision</span>
              <span className="text-xl font-bold font-mono text-emerald-700">{(evaluation.aggregate.precision * 100).toFixed(1)}%</span>
            </div>
            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <span className="text-[10px] font-mono text-emerald-800 uppercase block font-semibold">Recall</span>
              <span className="text-xl font-bold font-mono text-emerald-700">{(evaluation.aggregate.recall * 100).toFixed(1)}%</span>
            </div>
            <div className="p-3 bg-lavender-50 rounded-lg border border-lavender-200">
              <span className="text-[10px] font-mono text-lavender-800 uppercase block font-semibold">F1-Score</span>
              <span className="text-xl font-bold font-mono text-lavender-900">{(evaluation.aggregate.f1_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area: Findings Data Table & Filters */}
      <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
        {/* Filters Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-platinum-200 pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-platinum-400" />
            <h3 className="text-sm font-bold text-navy-950">LLIRE Anomaly Incidents</h3>
            <span className="text-xs text-platinum-500 font-mono">({totalCount} total)</span>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap w-full md:w-auto">
            {/* Category Filter */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono bg-white"
            >
              <option value="">All Categories</option>
              <option value="BALANCE_MISMATCH">Balance Mismatch</option>
              <option value="OVER_REDEMPTION">Over Redemption</option>
              <option value="UNREVERSED_RETURN">Unreversed Return</option>
              <option value="DOUBLE_EXPIRY">Double Expiry</option>
              <option value="INCORRECT_TIER">Incorrect Tier</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono bg-white"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono bg-white"
            >
              <option value="">All Statuses</option>
              <option value="DETECTED">Detected</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="RESOLVED">Resolved</option>
              <option value="DISMISSED">Dismissed</option>
            </select>

            <button
              onClick={() => loadAnomalies(currentPage)}
              className="p-1.5 border border-platinum-300 hover:bg-platinum-100 rounded-lg text-platinum-600 transition"
              title="Refresh findings"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingAnomalies ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Data Table */}
        {isLoadingAnomalies ? (
          <div className="p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
            Loading LLIRE incidents...
          </div>
        ) : anomalies.length === 0 ? (
          <div className="p-12 text-center text-platinum-500 text-xs">
            No anomaly incidents match the active filters.
          </div>
        ) : (
          <div className="border border-platinum-200 rounded-lg overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                <tr>
                  <th className="px-3 py-2.5">Incident ID</th>
                  <th className="px-3 py-2.5">Issue Type</th>
                  <th className="px-3 py-2.5">Severity</th>
                  <th className="px-3 py-2.5">Entity / Account</th>
                  <th className="px-3 py-2.5">Variance (PTS)</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-platinum-100 font-mono">
                {anomalies.map((inc) => (
                  <tr key={inc.incident_id} className="hover:bg-platinum-50/60 transition">
                    <td className="px-3 py-2.5 font-bold text-navy-950">
                      {inc.incident_id}
                    </td>
                    <td className="px-3 py-2.5 font-sans">
                      <span className="font-semibold text-navy-900 block">{String(inc.category || inc.issue_type).replace(/_/g, ' ')}</span>
                      <span className="text-[10px] text-platinum-500 font-mono truncate max-w-xs block">
                        {inc.description || inc.what_happened || 'Automated LLIRE detection'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        inc.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                        inc.severity === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                        inc.severity === 'MEDIUM' ? 'bg-lavender-100 text-lavender-800 border border-lavender-200' :
                        'bg-platinum-100 text-platinum-700'
                      }`}>
                        {inc.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-platinum-600">
                      {inc.account_id || inc.entity_id || 'System-Wide'}
                    </td>
                    <td className="px-3 py-2.5 font-bold text-navy-950">
                      {inc.variance_amount} PTS
                    </td>
                    <td className="px-3 py-2.5 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                        inc.status === 'DETECTED' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
                        inc.status === 'INVESTIGATING' ? 'bg-blue-50 text-blue-800 border border-blue-200' :
                        inc.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' :
                        'bg-platinum-100 text-platinum-700'
                      }`}>
                        {inc.status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-sans">
                      <button
                        onClick={() => handleInspectAnomaly(inc.incident_id)}
                        className="px-2.5 py-1 text-xs bg-lavender-50 hover:bg-lavender-100 text-lavender-900 border border-lavender-200 rounded-lg flex items-center gap-1 font-semibold ml-auto transition"
                      >
                        <Eye className="w-3.5 h-3.5" /> Explain
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center pt-2 text-xs text-platinum-600">
            <span>Page {currentPage} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={currentPage <= 1}
                onClick={() => loadAnomalies(currentPage - 1)}
                className="px-3 py-1 bg-platinum-100 hover:bg-platinum-200 disabled:opacity-40 rounded text-xs transition"
              >
                Previous
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => loadAnomalies(currentPage + 1)}
                className="px-3 py-1 bg-platinum-100 hover:bg-platinum-200 disabled:opacity-40 rounded text-xs transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* FORENSIC EXPLAINABILITY MODAL / DRAWER */}
      {selectedAnomaly && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-platinum-200 p-6 space-y-6 animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex justify-between items-start border-b border-platinum-200 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    selectedAnomaly.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                    selectedAnomaly.severity === 'HIGH' ? 'bg-amber-100 text-amber-800' :
                    'bg-lavender-100 text-lavender-800'
                  }`}>
                    {selectedAnomaly.severity}
                  </span>
                  <span className="font-mono text-xs text-platinum-500">{selectedAnomaly.incident_id}</span>
                </div>
                <h3 className="text-lg font-bold text-navy-950 mt-1">
                  Forensic Intelligence Breakdown: {String(selectedAnomaly.category || selectedAnomaly.issue_type).replace(/_/g, ' ')}
                </h3>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="p-1 rounded-lg text-platinum-400 hover:text-navy-950 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* The 7 Mandatory Explainability Answers */}
            <div className="space-y-4 text-xs">
              {/* 1. What Happened */}
              <div className="p-3.5 bg-platinum-50 rounded-lg border border-platinum-200">
                <span className="font-bold text-navy-950 block text-xs mb-1">1. What Happened?</span>
                <p className="text-platinum-700 leading-relaxed">
                  {selectedAnomaly.what_happened || selectedAnomaly.description || 'Automated LLIRE detection flagged an accounting anomaly.'}
                </p>
              </div>

              {/* 2. Target Entity & Detector */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
                  <span className="font-bold text-navy-950 block mb-0.5">2. Target Entity</span>
                  <span className="font-mono text-lavender-900 font-semibold">{selectedAnomaly.account_id || selectedAnomaly.entity_id || 'System-Wide Ledger'}</span>
                </div>
                <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
                  <span className="font-bold text-navy-950 block mb-0.5">Originating Detector</span>
                  <span className="font-mono text-platinum-800">{selectedAnomaly.detector_id || selectedAnomaly.detector_name || 'LLIRE-Core'}</span>
                </div>
              </div>

              {/* 3 & 4. Why Anomalous & Threshold Exceeded */}
              <div className="p-3.5 bg-lavender-50/60 rounded-lg border border-lavender-200">
                <span className="font-bold text-navy-950 block mb-1">3. Why Anomalous & 4. Invariant Rule Violated</span>
                <p className="text-platinum-800 leading-relaxed font-mono text-[11px]">
                  Rule Violated: <strong className="text-lavender-900">{selectedAnomaly.rule_violated || selectedAnomaly.severity_reason || 'Accounting invariant condition failed.'}</strong>
                </p>
              </div>

              {/* 5. Financial Exposure */}
              <div className="p-3 bg-rose-50/50 rounded-lg border border-rose-200">
                <span className="font-bold text-rose-900 block mb-0.5">5. Variance / Points at Risk</span>
                <span className="text-base font-bold font-mono text-rose-700">
                  {selectedAnomaly.variance_amount} PTS
                </span>
              </div>

              {/* 6. Supporting Evidence Payload */}
              <div className="space-y-1">
                <span className="font-bold text-navy-950 block">6. Forensic Evidence Data Payload</span>
                <div className="p-3 bg-navy-950 rounded-lg text-platinum-200 font-mono text-[11px] overflow-x-auto max-h-40 border border-navy-800">
                  <pre>{JSON.stringify(selectedAnomaly.evidence || selectedAnomaly.discrepancy_calculation || {}, null, 2)}</pre>
                </div>
              </div>

              {/* 7. Recommended Investigation / Remediation Action */}
              <div className="p-3.5 bg-amber-50/60 rounded-lg border border-amber-200 text-amber-950">
                <span className="font-bold block mb-1">7. Recommended Remediation Action</span>
                <p className="leading-relaxed">
                  {selectedAnomaly.recommendation || 'Route to Operations Manager console for dual-key review.'}
                </p>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end gap-3 pt-2 border-t border-platinum-200">
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="px-4 py-2 bg-platinum-100 hover:bg-platinum-200 text-navy-950 rounded-lg text-xs font-semibold transition"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
