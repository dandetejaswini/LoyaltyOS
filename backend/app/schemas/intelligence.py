from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class AnomalyEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")


class AnomalyDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    issue_type: str
    entity_type: str
    entity_id: str
    variance_amount: Decimal
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    # Granular Explainability Fields (extracted from details payload)
    detector_id: Optional[str] = None
    severity: str = "MEDIUM"
    severity_reason: Optional[str] = None
    rule_violated: Optional[str] = None
    what_happened: Optional[str] = None
    description: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    discrepancy_calculation: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    fingerprint: Optional[str] = None


class AnomalyListPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[AnomalyDetailResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class DetectionRunRequest(BaseModel):
    account_id: Optional[str] = Field(None, description="Optional account ID to scope detection to a single account")
    include_detectors: Optional[List[str]] = Field(None, description="Optional subset of detector IDs to execute")


class DetectionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    executed_at: datetime
    detectors_run: List[str]
    total_anomalies_detected: int
    new_incidents_created: int
    existing_incidents_skipped: int
    incidents: List[AnomalyDetailResponse]


class CategoryCount(BaseModel):
    category: str
    count: int


class SeverityCount(BaseModel):
    severity: str
    count: int


class IntelligenceSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_incidents: int
    open_incidents: int
    investigating_incidents: int
    resolved_incidents: int
    dismissed_incidents: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    last_run_at: Optional[datetime] = None


class CategoryEvaluationMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


class EngineEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluated_at: datetime
    dataset_scale: str
    total_ground_truth_anomalies: int
    total_detected_anomalies: int
    categories: Dict[str, CategoryEvaluationMetrics]
    aggregate: CategoryEvaluationMetrics
