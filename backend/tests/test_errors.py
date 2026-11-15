import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_not_found_returns_rfc7807(client: AsyncClient):
    """Verify 404 returns RFC-7807 compliant ProblemDetails JSON."""
    response = await client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "title" in data
    assert "status" in data
    assert data["status"] == 404
    assert "timestamp" in data
    assert "instance" in data
    assert data["instance"] == "/api/v1/non-existent-endpoint"
