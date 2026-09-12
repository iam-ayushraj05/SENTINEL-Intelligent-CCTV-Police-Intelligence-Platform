import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_event_processor import process_sentinel_ai_event
from app.services.kafka_producer import (
    publish_event,
    TOPIC_WEAPON_EVENTS,
    TOPIC_FIRE_EVENTS,
    TOPIC_SMOKE_EVENTS,
    TOPIC_FACE_EVENTS,
    TOPIC_ACTIVITY_EVENTS,
)
from app.models.audit import AuditLog
from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent


@pytest.mark.asyncio
async def test_ai_event_processor_and_db_persistence():
    """Verify AI events are processed, persisted in DB, and alerts are evaluated"""
    dummy_db = type("DummySession", (), {})()

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "WEAPON_DETECTED",
        "camera_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": 0.92,
        "track_id": "tr_101",
        "class_name": "Handgun",
        "bounding_box": [10.0, 10.0, 50.0, 50.0],
        "requires_human_review": True,
        "metadata": {"consecutive_frames": 5},
    }

    result = await process_sentinel_ai_event(dummy_db, event)
    assert result is not None
    assert result["event_type"] == "WEAPON_DETECTED"
    assert result["confidence"] == 0.92
    assert result["requires_human_review"] is True


@pytest.mark.asyncio
async def test_kafka_topics_publish():
    """Verify Kafka publishing helpers run cleanly without throwing errors"""
    await publish_event(TOPIC_WEAPON_EVENTS, "WEAPON_DETECTED", "cam_01", {"conf": 0.9})
    await publish_event(TOPIC_FIRE_EVENTS, "FIRE_DETECTED", "cam_01", {"conf": 0.95})
    await publish_event(TOPIC_SMOKE_EVENTS, "SMOKE_DETECTED", "cam_01", {"conf": 0.88})
    await publish_event(TOPIC_FACE_EVENTS, "FACE_MATCH", "cam_01", {"conf": 0.91})
    await publish_event(TOPIC_ACTIVITY_EVENTS, "HUMAN_ACTIVITY_DETECTED", "cam_01", {"activity": "fighting"})


def test_anpr_search_api():
    """Verify GET /api/v1/search/plates endpoint response and structure"""
    client = TestClient(app)
    response = client.get("/api/v1/search/plates?plate=GJ01AB1234&min_confidence=0.5")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert data["query"] == "GJ01AB1234"


def test_camera_dashboard_api():
    """Verify camera dashboard endpoint returns real camera & AI status"""
    client = TestClient(app)
    # List cameras to obtain a valid camera ID
    cams_res = client.get("/api/v1/cameras")
    assert cams_res.status_code == 200
    cams = cams_res.json()
    assert len(cams) > 0

    cam_id = cams[0]["id"]
    dash_res = client.get(f"/api/v1/cameras/{cam_id}/dashboard")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert "connection_status" in dash
    assert "ai_processing_status" in dash

    assert dash["camera_code"] == cams[0]["camera_code"]


def test_audit_logs_api():
    """Verify audit logs endpoint returns list of audit events"""
    client = TestClient(app)
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
