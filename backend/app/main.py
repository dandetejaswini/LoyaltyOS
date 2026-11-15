from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.errors import register_exception_handlers
from backend.app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    yield
    # Shutdown logic
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Auditable, double-entry financial loyalty ledger platform for enterprise point accrual, redemption, expiration, and reversal.",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS with explicit origins and restricted regex (credentials enabled safely)
    origins = settings.ALLOWED_ORIGINS
    if isinstance(origins, str):
        origins = [origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=settings.ALLOW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Idempotency-Key", "X-Cache-Lookup"],
    )

    # Register centralized exception handlers (RFC-7807 compliant)
    register_exception_handlers(app)

    # Mount API v1 router (and alias at /v1 for serverless proxy rewrites)
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)
    if settings.API_V1_STR != "/v1":
        app.include_router(api_v1_router, prefix="/v1", include_in_schema=False)

    @app.get("/", tags=["Root"])
    @app.get("/api", tags=["Root"], include_in_schema=False)
    @app.get("/api/", tags=["Root"], include_in_schema=False)
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs",
            "health_url": f"{settings.API_V1_STR}/health",
            "liveness_url": f"{settings.API_V1_STR}/health/live",
            "readiness_url": f"{settings.API_V1_STR}/health/ready",
            "environment": settings.APP_ENV,
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
