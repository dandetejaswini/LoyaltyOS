import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verify general health check endpoint returns 200 and truthful status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Structure checks
    assert "status" in data
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "database" in data
    assert "timestamp" in data

    # Verify LoyaltyOS app metadata
    assert "LoyaltyOS" in data["app_name"]
    assert data["version"] == "1.0.0"

    # Truthful database status verification
    db_report = data["database"]
    assert "connected" in db_report
    assert "status" in db_report
    assert db_report["connected"] is False
    assert db_report["status"] == "not_configured"


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Verify liveness probe returns 200 and status alive."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_probe_reports_not_ready_when_db_unconfigured(client: AsyncClient):
    """Verify readiness probe returns 503 and not_ready when required database is unconfigured."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["ready"] is False
    assert data["database"]["connected"] is False
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify root endpoint returns API metadata and probe documentation links."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "LoyaltyOS" in data["name"]
    assert data["docs_url"] == "/api/v1/docs"
    assert data["health_url"] == "/api/v1/health"
    assert data["liveness_url"] == "/api/v1/health/live"
    assert data["readiness_url"] == "/api/v1/health/ready"
