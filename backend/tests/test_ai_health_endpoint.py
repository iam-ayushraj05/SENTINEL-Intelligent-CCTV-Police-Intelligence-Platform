import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_ai_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/health/ai")
    assert response.status_code == 200
    data = response.json()
    assert "ai_status" in data
    assert "gpu_available" in data
    assert "capabilities" in data
    assert "person_detection" in data["capabilities"]


def test_existing_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
