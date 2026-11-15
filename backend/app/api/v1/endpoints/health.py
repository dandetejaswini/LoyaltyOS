from fastapi import APIRouter, status
from backend.app.schemas.common import HealthResponse
from backend.app.core.config import settings
from backend.app.core.database import check_database_connection

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health and Status Check",
    description="Returns the truthful runtime health status of the application, version metadata, and database connection state."
)
async def get_health():
    db_status = await check_database_connection()
    overall_status = "healthy"
    if db_status.get("status") == "disconnected":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database=db_status,
    )
