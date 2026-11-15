import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_headers_for_local_frontend_origin(client: AsyncClient):
    """Verify CORS middleware responds with correct headers for local Vite frontend preflight."""
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
async def test_cors_headers_for_vercel_preview_origin(client: AsyncClient):
    """Verify CORS middleware allows Vercel preview domains via restricted origin regex."""
    headers = {
        "Origin": "https://loyaltyos-preview-123.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type, Idempotency-Key",
    }
    response = await client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://loyaltyos-preview-123.vercel.app"


@pytest.mark.asyncio
async def test_cors_rejects_unauthorized_external_origin(client: AsyncClient):
    """Verify CORS middleware does NOT grant credentials/access-control-allow-origin to random domains."""
    headers = {
        "Origin": "https://malicious-external-site.com",
        "Access-Control-Request-Method": "GET",
    }
    response = await client.options("/api/v1/health", headers=headers)
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_health_check_via_frontend_origin(client: AsyncClient):
    """Verify standard GET request with Origin header receives access-control-allow-origin and exposed headers."""
    headers = {"Origin": "http://localhost:5173"}
    response = await client.get("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-expose-headers" in response.headers
    assert "Idempotency-Key" in response.headers.get("access-control-expose-headers", "")
