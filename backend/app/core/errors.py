from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from backend.app.schemas.common import ProblemDetails
from backend.app.core.logging import logger


class UnauthorizedError(FastAPIHTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


class ForbiddenError(FastAPIHTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(FastAPIHTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(FastAPIHTTPException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestError(FastAPIHTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


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
        headers = dict(getattr(exc, "headers", None) or {})
        headers.setdefault("Content-Type", "application/problem+json")
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(),
            headers=headers,
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
