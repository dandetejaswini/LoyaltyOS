import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditEvent, RejectedOperation
from backend.app.core.logging import logger


class AuditService:
    """
    Forensic audit logging and rejection recording.
    Guarantees that security events and rejected transactions are safely logged
    without mutating the immutable points ledger.
    """

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    async def log_event(
        cls,
        db: AsyncSession,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=cls.generate_id("AUD"),
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_payload=metadata or {},
            ip_address=ip_address,
        )
        db.add(event)
        logger.info(f"[AUDIT] {action} on {entity_type}:{entity_id} by {actor_id}")
        return event

    @classmethod
    async def log_rejection(
        cls,
        db: AsyncSession,
        actor_id: str,
        operation_type: str,
        error_code: str,
        error_message: str,
        account_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RejectedOperation:
        rejection = RejectedOperation(
            operation_id=cls.generate_id("REJ"),
            account_id=account_id,
            actor_id=actor_id,
            operation_type=operation_type,
            error_code=error_code,
            error_message=error_message,
            payload=payload or {},
        )
        db.add(rejection)
        logger.warning(f"[REJECTION] {operation_type} rejected ({error_code}) for account={account_id} by {actor_id}: {error_message}")
        return rejection
