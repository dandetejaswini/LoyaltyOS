import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_headers_for_frontend_origin(client: AsyncClient):
    """Verify CORS middleware responds with correct headers for Vite frontend preflight."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type, Idempotency-Key",
    }
    response = await client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


@pytest.mark.asyncio
async def test_health_check_via_frontend_origin(client: AsyncClient):
    """Verify standard GET request with Origin header receives access-control-allow-origin and exposed headers."""
    headers = {"Origin": "http://localhost:5173"}
    response = await client.get("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-expose-headers" in response.headers
    assert "Idempotency-Key" in response.headers.get("access-control-expose-headers", "")
