/**
 * LoyaltyOS — Intelligence & Reconciliation Engine (LLIRE) Types
 * Phase 5 Response Contracts for Frontend Consumption
 */

export type AnomalySeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type AnomalyStatus = 'DETECTED' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';

export type AnomalyCategory = 
  | 'BALANCE_MISMATCH'
  | 'OVER_REDEMPTION'
  | 'UNREVERSED_RETURN'
  | 'DOUBLE_EXPIRY'
  | 'INCORRECT_TIER';

export interface AnomalyDetail {
  incident_id: string;
  issue_type: AnomalyCategory | string;
  entity_type: string;
  entity_id: string;
  variance_amount: string | number;
  status: AnomalyStatus;
  created_at: string;
  resolved_at: string | null;

  // Explainability & Forensic Evidence
  detector_id?: string;
  severity: AnomalySeverity;
  severity_reason?: string;
  rule_violated?: string;
  what_happened?: string;
  description?: string;
  evidence?: Record<string, any>;
  discrepancy_calculation?: Record<string, any>;
  recommendation?: string;
  fingerprint?: string;
}

export interface AnomalyListPage {
  items: AnomalyDetail[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DetectionRunResponse {
  run_id: string;
  executed_at: string;
  detectors_run: string[];
  total_anomalies_detected: number;
  new_incidents_created: number;
  existing_incidents_skipped: number;
  incidents: AnomalyDetail[];
}

export interface IntelligenceSummary {
  total_incidents: number;
  open_incidents: number;
  investigating_incidents: number;
  resolved_incidents: number;
  dismissed_incidents: number;
  by_severity: Record<AnomalySeverity, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  last_run_at: string | null;
}

export interface CategoryEvaluationMetrics {
  category: string;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface EngineEvaluationResponse {
  evaluated_at: string;
  dataset_scale: string;
  total_ground_truth_anomalies: number;
  total_detected_anomalies: number;
  categories: Record<string, CategoryEvaluationMetrics>;
  aggregate: CategoryEvaluationMetrics;
}
