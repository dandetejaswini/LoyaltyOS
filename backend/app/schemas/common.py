from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def get_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProblemDetails(BaseModel):
    """RFC-7807 compliant problem details object."""
    type: str = Field(default="about:blank", description="URI reference identifying the problem type")
    title: str = Field(description="Short human-readable summary of the problem")
    status: int = Field(description="HTTP status code")
    detail: Optional[str] = Field(default=None, description="Human-readable explanation specific to this occurrence")
    instance: Optional[str] = Field(default=None, description="URI reference identifying the specific occurrence")
    timestamp: str = Field(default_factory=get_utc_iso)
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed validation errors if applicable")


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Truthful service status: healthy | degraded | unhealthy")
    app_name: str
    version: str
    environment: str
    database: Dict[str, Any] = Field(description="Truthful database status and connectivity report")
    timestamp: str = Field(default_factory=get_utc_iso)


class StandardResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: str = Field(default_factory=get_utc_iso)
