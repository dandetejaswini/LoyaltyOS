import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verify health check endpoint returns 200 and truthful status."""
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

    # Verify app metadata
    assert data["app_name"] == "YottaFlex Loyalty Ledger"
    assert data["version"] == "1.0.0"

    # Truthful database status verification
    db_report = data["database"]
    assert "connected" in db_report
    assert "status" in db_report
    # In Phase 1 without DATABASE_URL, it must report not_configured and connected=False
    assert db_report["connected"] is False
    assert db_report["status"] == "not_configured"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify root endpoint returns API metadata and documentation links."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "YottaFlex Loyalty Ledger"
    assert data["docs_url"] == "/api/v1/docs"
    assert data["health_url"] == "/api/v1/health"
