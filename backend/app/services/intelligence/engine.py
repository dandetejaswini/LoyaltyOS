import uuid
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.app.models.audit import AnomalyIncident
from backend.app.schemas.intelligence import (
    AnomalyDetailResponse,
    AnomalyListPage,
    DetectionRunResponse,
    IntelligenceSummaryResponse,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.intelligence.base import BaseDetector, AnomalyFinding
from backend.app.services.intelligence.balance_mismatch import BalanceMismatchDetector
from backend.app.services.intelligence.over_redemption import OverRedemptionDetector
from backend.app.services.intelligence.unreversed_return import UnreversedReturnDetector
from backend.app.services.intelligence.double_expiry import DoubleExpiryDetector
from backend.app.services.intelligence.incorrect_tier import IncorrectTierDetector
from backend.app.core.errors import NotFoundError
from backend.app.core.logging import logger


class IntelligenceEngine:
    """
    LLIRE: Loyalty Ledger Intelligence & Reconciliation Engine.
    Orchestrates execution of the 5 mandatory anomaly detectors, enforces
    idempotent incident persistence, and generates explainable audit-ready findings.
    Never mutates the append-only financial ledger.
    """

    def __init__(self):
        self.detectors: Dict[str, BaseDetector] = {
            "DET-BALANCE-MISMATCH": BalanceMismatchDetector(),
            "DET-OVER-REDEMPTION": OverRedemptionDetector(),
            "DET-UNREVERSED-RETURN": UnreversedReturnDetector(),
            "DET-DOUBLE-EXPIRY": DoubleExpiryDetector(),
            "DET-INCORRECT-TIER": IncorrectTierDetector(),
        }
        # Category alias lookup
        self.category_to_detector = {
            "BALANCE_MISMATCH": "DET-BALANCE-MISMATCH",
            "OVER_REDEMPTION": "DET-OVER-REDEMPTION",
            "UNREVERSED_RETURN": "DET-UNREVERSED-RETURN",
            "DOUBLE_EXPIRY": "DET-DOUBLE-EXPIRY",
            "INCORRECT_TIER": "DET-INCORRECT-TIER",
            "GROSS_SPEND_TIER_CALCULATION": "DET-INCORRECT-TIER",
        }

    def _resolve_detector_ids(self, requested_names: Optional[List[str]]) -> List[str]:
        if not requested_names:
            return list(self.detectors.keys())

        resolved = []
        for name in requested_names:
            norm = name.strip().upper().replace("-", "_")
            if norm in self.detectors:
                resolved.append(norm)
            elif norm in self.category_to_detector:
                resolved.append(self.category_to_detector[norm])
            else:
                # Check for partial key match
                for det_id in self.detectors:
                    if norm in det_id or norm in det_id.replace("DET_", ""):
                        resolved.append(det_id)
                        break
        return resolved or list(self.detectors.keys())

    @classmethod
    def _finding_to_response(cls, incident: AnomalyIncident) -> AnomalyDetailResponse:
        details = incident.details or {}
        return AnomalyDetailResponse(
            incident_id=incident.incident_id,
            issue_type=incident.issue_type,
            entity_type=incident.entity_type,
            entity_id=incident.entity_id,
            variance_amount=incident.variance_amount,
            status=incident.status,
            created_at=incident.created_at or datetime.now(timezone.utc),
            resolved_at=incident.resolved_at,
            detector_id=details.get("detector_id"),
            severity=details.get("severity", "MEDIUM"),
            severity_reason=details.get("severity_reason"),
            rule_violated=details.get("rule_violated"),
            what_happened=details.get("what_happened"),
            description=details.get("description"),
            evidence=details.get("evidence"),
            discrepancy_calculation=details.get("discrepancy_calculation"),
            recommendation=details.get("recommendation"),
            fingerprint=details.get("fingerprint"),
        )

    async def run_detection(
        self,
        db: AsyncSession,
        actor_id: str,
        account_id: Optional[str] = None,
        detector_names: Optional[List[str]] = None,
    ) -> DetectionRunResponse:
        run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc)
        target_detector_ids = self._resolve_detector_ids(detector_names)

        all_findings: List[AnomalyFinding] = []
        executed_detectors: List[str] = []

        # 1. Execute detectors sequentially on the session
        for det_id in target_detector_ids:
            detector = self.detectors.get(det_id)
            if not detector:
                continue
            executed_detectors.append(detector.name)
            try:
                findings = await detector.detect(db, account_id=account_id)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Detector {det_id} execution failed: {e}")

        new_incidents_count = 0
        skipped_duplicates_count = 0
        persisted_incidents: List[AnomalyIncident] = []

        # 2. Idempotently persist findings to anomaly_incidents
        for finding in all_findings:
            # Query existing open incident matching entity and issue_type
            existing_stmt = select(AnomalyIncident).where(
                AnomalyIncident.issue_type == finding.category,
                AnomalyIncident.entity_type == finding.entity_type,
                AnomalyIncident.entity_id == finding.entity_id,
                AnomalyIncident.status.in_(["DETECTED", "INVESTIGATING"]),
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing_fp = (existing.details or {}).get("fingerprint")
                if existing_fp == finding.fingerprint:
                    skipped_duplicates_count += 1
                    persisted_incidents.append(existing)
                    continue

            # Create new incident record
            incident_id = f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            incident = AnomalyIncident(
                incident_id=incident_id,
                issue_type=finding.category,
                entity_type=finding.entity_type,
                entity_id=finding.entity_id,
                variance_amount=finding.variance_amount,
                details=finding.to_details_payload(),
                status="DETECTED",
                created_at=now,
                resolved_at=None,
            )
            db.add(incident)
            persisted_incidents.append(incident)
            new_incidents_count += 1

        # 3. Commit transaction
        await db.commit()

        # 4. Dispatch forensic audit event
        try:
            await AuditService.log_event(
                db=db,
                actor_id=actor_id,
                action="INTELLIGENCE_DETECTION_RUN",
                entity_type="INTELLIGENCE_RUN",
                entity_id=run_id,
                metadata={
                    "run_id": run_id,
                    "account_id": account_id,
                    "detectors_run": executed_detectors,
                    "total_anomalies_detected": len(all_findings),
                    "new_incidents_created": new_incidents_count,
                    "existing_incidents_skipped": skipped_duplicates_count,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to record intelligence run audit event: {e}")

        response_items = [self._finding_to_response(inc) for inc in persisted_incidents]

        return DetectionRunResponse(
            run_id=run_id,
            executed_at=now,
            detectors_run=executed_detectors,
            total_anomalies_detected=len(all_findings),
            new_incidents_created=new_incidents_count,
            existing_incidents_skipped=skipped_duplicates_count,
            incidents=response_items,
        )

    async def get_incidents(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AnomalyListPage:
        query = select(AnomalyIncident)

        if category:
            query = query.where(AnomalyIncident.issue_type == category.upper().strip())
        if status:
            query = query.where(AnomalyIncident.status == status.upper().strip())
        if entity_type:
            query = query.where(AnomalyIncident.entity_type == entity_type.upper().strip())
        if entity_id:
            query = query.where(AnomalyIncident.entity_id == entity_id.strip())

        # Total count
        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Pagination (order by created_at DESC)
        offset = (page - 1) * page_size
        paged_query = query.order_by(desc(AnomalyIncident.created_at)).offset(offset).limit(page_size)
        incidents = (await db.execute(paged_query)).scalars().all()

        items = [self._finding_to_response(inc) for inc in incidents]

        # Optional severity filter post-load if JSONB query differs across SQLite/PG
        if severity:
            sev_target = severity.upper().strip()
            items = [item for item in items if item.severity == sev_target]
            total_count = len(items)

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return AnomalyListPage(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_incident_by_id(
        self,
        db: AsyncSession,
        incident_id: str,
    ) -> AnomalyDetailResponse:
        stmt = select(AnomalyIncident).where(AnomalyIncident.incident_id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError(detail=f"Anomaly incident '{incident_id}' not found.")
        return self._finding_to_response(incident)

    async def get_summary(
        self,
        db: AsyncSession,
    ) -> IntelligenceSummaryResponse:
        incidents = (await db.execute(select(AnomalyIncident))).scalars().all()

        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        by_category: Dict[str, int] = {}
        by_status = {"DETECTED": 0, "INVESTIGATING": 0, "RESOLVED": 0, "DISMISSED": 0}

        latest_time = None

        for inc in incidents:
            # Status
            st = inc.status.upper()
            by_status[st] = by_status.get(st, 0) + 1

            # Category
            cat = inc.issue_type
            by_category[cat] = by_category.get(cat, 0) + 1

            # Severity from details
            sev = (inc.details or {}).get("severity", "MEDIUM").upper()
            by_severity[sev] = by_severity.get(sev, 0) + 1

            if latest_time is None or inc.created_at > latest_time:
                latest_time = inc.created_at

        return IntelligenceSummaryResponse(
            total_incidents=len(incidents),
            open_incidents=by_status.get("DETECTED", 0),
            investigating_incidents=by_status.get("INVESTIGATING", 0),
            resolved_incidents=by_status.get("RESOLVED", 0),
            dismissed_incidents=by_status.get("DISMISSED", 0),
            by_severity=by_severity,
            by_category=by_category,
            by_status=by_status,
            last_run_at=latest_time,
        )


# Singleton instance
intelligence_engine = IntelligenceEngine()
