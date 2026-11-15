from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from backend.app.schemas.common import ProblemDetails
from backend.app.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    async def common_http_handler(request: Request, exc: StarletteHTTPException | FastAPIHTTPException):
        logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        problem = ProblemDetails(
            type="https://yottaflex.io/errors/http-error",
            title=exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(),
            headers=getattr(exc, "headers", None) or {"Content-Type": "application/problem+json"},
        )

    app.add_exception_handler(FastAPIHTTPException, common_http_handler)
    app.add_exception_handler(StarletteHTTPException, common_http_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        problem = ProblemDetails(
            type="https://yottaflex.io/errors/validation-error",
            title="Request Validation Failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The incoming request failed schema validation rules.",
            instance=str(request.url.path),
            errors=[
                {
                    "loc": [str(loc) for loc in err.get("loc", [])],
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
                for err in exc.errors()
            ],
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=problem.model_dump(),
            headers={"Content-Type": "application/problem+json"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled internal error on {request.method} {request.url.path}: {str(exc)}")
        problem = ProblemDetails(
            type="https://yottaflex.io/errors/internal-server-error",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred. Please contact system support.",
            instance=str(request.url.path),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(),
            headers={"Content-Type": "application/problem+json"},
        )
