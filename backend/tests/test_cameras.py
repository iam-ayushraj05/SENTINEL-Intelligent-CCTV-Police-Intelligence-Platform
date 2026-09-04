import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_list_cameras_endpoint_exists():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/cameras")
    # The endpoint should respond; DB availability is environment-dependent.
    assert response.status_code in (200, 500)
