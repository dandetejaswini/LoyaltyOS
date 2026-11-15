from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_role
from backend.app.models.identity import AppUser
from backend.app.models.loyalty import Customer, LoyaltyAccount
from backend.app.schemas.intelligence import (
    AnomalyDetailResponse,
    AnomalyListPage,
    DetectionRunRequest,
    DetectionRunResponse,
    IntelligenceSummaryResponse,
    EngineEvaluationResponse,
)
from backend.app.services.intelligence.engine import intelligence_engine
from backend.app.services.intelligence.evaluator import IntelligenceEvaluator
from backend.app.core.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/intelligence", tags=["Intelligence & Reconciliation Engine (LLIRE)"])

# Roles authorized for intelligence operations
require_intelligence_analyst = require_role(["ANALYST", "OPERATOR", "OPERATIONS_MANAGER"])


@router.post("/detect", response_model=DetectionRunResponse)
async def run_all_detectors(
    payload: Optional[DetectionRunRequest] = None,
    current_user: AppUser = Depends(require_intelligence_analyst),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes all 5 LLIRE anomaly detectors across the organization or scoped to an account.
    Idempotently persists findings without mutating the append-only transaction ledger.
    Authorized for ANALYST, OPERATOR, and OPERATIONS_MANAGER roles.
    """
    account_id = payload.account_id if payload else None
    include_detectors = payload.include_detectors if payload else None

    return await intelligence_engine.run_detection(
        db=db,
        actor_id=str(current_user.id),
        account_id=account_id,
        detector_names=include_detectors,
    )


@router.post("/detect/{detector_name}", response_model=DetectionRunResponse)
async def run_single_detector(
    detector_name: str = Path(..., description="Target detector (balance-mismatch, over-redemption, unreversed-return, double-expiry, incorrect-tier)"),
    account_id: Optional[str] = Query(None, description="Optional account ID to scope detection"),
    current_user: AppUser = Depends(require_intelligence_analyst),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a single designated anomaly detector.
    """
    return await intelligence_engine.run_detection(
        db=db,
        actor_id=str(current_user.id),
        account_id=account_id,
        detector_names=[detector_name],
    )


@router.get("/anomalies", response_model=AnomalyListPage)
async def list_anomalies(
    category: Optional[str] = Query(None, description="Filter by anomaly category"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    status: Optional[str] = Query(None, description="Filter by status (DETECTED, INVESTIGATING, RESOLVED, DISMISSED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves paginated anomaly findings with filtering.
    Customers are strictly restricted to their own account's findings.
    """
    filter_entity_id = None
    if current_user.role == "CUSTOMER":
        # Resolve customer loyalty account
        stmt = (
            select(LoyaltyAccount.account_id)
            .join(Customer, Customer.customer_id == LoyaltyAccount.customer_id)
            .where(Customer.user_id == current_user.id)
        )
        acc_id = (await db.execute(stmt)).scalar_one_or_none()
        if not acc_id:
            return AnomalyListPage(items=[], total_count=0, page=page, page_size=page_size, total_pages=1)
        filter_entity_id = acc_id

    return await intelligence_engine.get_incidents(
        db=db,
        category=category,
        severity=severity,
        status=status,
        entity_id=filter_entity_id,
        page=page,
        page_size=page_size,
    )


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyDetailResponse)
async def get_anomaly_detail(
    anomaly_id: str = Path(..., description="Unique incident ID"),
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full explainability, forensic evidence, and recommended investigation actions
    for a specific anomaly incident.
    """
    incident = await intelligence_engine.get_incident_by_id(db, anomaly_id)

    # Customer isolation check
    if current_user.role == "CUSTOMER":
        stmt = (
            select(LoyaltyAccount.account_id)
            .join(Customer, Customer.customer_id == LoyaltyAccount.customer_id)
            .where(Customer.user_id == current_user.id)
        )
        acc_id = (await db.execute(stmt)).scalar_one_or_none()
        if incident.entity_id != acc_id and incident.evidence.get("account_id") != acc_id:
            raise ForbiddenError(detail="Access denied: You do not have permission to view this incident.")

    return incident


@router.get("/summary", response_model=IntelligenceSummaryResponse)
async def get_intelligence_summary(
    current_user: AppUser = Depends(require_intelligence_analyst),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated organization-wide intelligence metrics, open incident counts,
    and distributions across severity and categories.
    """
    return await intelligence_engine.get_summary(db)


@router.get("/evaluate", response_model=EngineEvaluationResponse)
async def evaluate_engine_accuracy(
    current_user: AppUser = Depends(require_intelligence_analyst),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates detector performance against Phase 3 labelled ground-truth manifests.
    Returns True Positives, False Positives, False Negatives, Precision, Recall, and F1.
    """
    return await IntelligenceEvaluator.evaluate(db)
