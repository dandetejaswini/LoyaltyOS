from fastapi import APIRouter, status, Response
from fastapi.responses import JSONResponse
from backend.app.schemas.common import HealthResponse, LivenessResponse, ReadinessResponse
from backend.app.core.config import settings
from backend.app.core.database import check_database_connection

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="General Service Health Check",
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


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Liveness Check",
    description="Liveness probe verifying that the FastAPI server process is running and responding."
)
async def get_liveness():
    return LivenessResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Application Readiness Check",
    description="Readiness probe verifying that the application and its required dependencies (database) are ready to accept traffic. Returns 503 if required database is not connected."
)
async def get_readiness():
    db_status = await check_database_connection()
    is_ready = db_status.get("connected", False)

    response_data = ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        ready=is_ready,
        database=db_status,
    )

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data.model_dump(),
        )

    return response_data
