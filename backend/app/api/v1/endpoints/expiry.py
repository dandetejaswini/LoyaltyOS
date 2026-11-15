from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.api.deps import require_operator
from backend.app.models.identity import AppUser
from backend.app.schemas.ledger import ExpiryExecutionRequest, ExpiryBatchResponse
from backend.app.services.expiry_service import ExpiryService

router = APIRouter(prefix="/expiry", tags=["Points Lot Expiration"])


@router.post("/execute", response_model=ExpiryBatchResponse, status_code=status.HTTP_200_OK)
async def execute_points_expiry_batch(
    req: ExpiryExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(require_operator),
):
    """
    Workflow F: Idempotent Batch Points Expiration.
    Identifies lots whose 365-day validity has elapsed, expires unconsumed points,
    and appends immutable EXPIRY debit journal entries.
    Restricted to Operator and Operations Manager roles.
    """
    return await ExpiryService.process_expiries(
        db=db,
        req=req,
        actor_id=str(current_user.id),
    )
