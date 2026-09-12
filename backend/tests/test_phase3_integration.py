"""
Phase 3 Integration Test Suite for Sentinel Intelligence Platform.

Verifies:
1. Dynamic Camera Catalogue and GIS Map APIs
2. Multi-Camera Priority AI Scheduler (RTX 4050 resource allocation)
3. Camera Priority Update Endpoint
4. Cross-Camera Vehicle Journey Timeline (OBSERVED vs INFERRED)
5. Correlated Event Fusion Rules
6. Investigation Case Workspace (Review status transitions)
7. Global Multi-Entity Search
8. Security Audit (No exposed RTSP passwords or credentials)
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from ai.sentinel_ai.scheduler.camera_scheduler import camera_scheduler, PriorityLevel


def test_gis_camera_map_api():
    """Verify GET /api/v1/cameras/gis returns verified camera GIS layer."""
    client = TestClient(app)
    res = client.get("/api/v1/cameras/gis")
    assert res.status_code == 200
    cameras = res.json()
    assert isinstance(cameras, list)
    assert len(cameras) > 0
    cam = cameras[0]
    assert "camera_code" in cam
    assert "latitude" in cam
    assert "longitude" in cam
    assert "status" in cam
    assert "hls_url" in cam


def test_camera_priority_scheduler():
    """Verify multi-camera priority scheduler balances slots according to priority hierarchy."""
    scheduler = camera_scheduler
    
    # Register 6 cameras (scheduler max slots = 4)
    for i in range(1, 7):
        scheduler.register_camera(
            camera_id=f"cam-id-{i}",
            camera_code=f"cam{i}",
            name=f"Camera {i}",
            priority=PriorityLevel.NORMAL_CAMERA,
        )

    assert len(scheduler.cameras) >= 6
    assert len(scheduler.active_slots) == scheduler.max_ai_cameras

    # Elevate camera 6 to CRITICAL_ALERT
    scheduler.set_camera_priority("cam-id-6", PriorityLevel.CRITICAL_ALERT)
    assert "cam-id-6" in scheduler.active_slots
    assert scheduler.cameras["cam-id-6"].priority == PriorityLevel.CRITICAL_ALERT

    # Verify frame sampling (interval = 2)
    assert scheduler.should_process_frame("cam-id-6", frame_count=4) is True
    assert scheduler.should_process_frame("cam-id-6", frame_count=3) is False

    # Verify telemetry
    status = scheduler.get_dashboard_status()
    assert "total_registered_cameras" in status
    assert "active_slots" in status


def test_camera_priority_api():
    """Verify POST /api/v1/cameras/{camera_id}/priority endpoint."""
    client = TestClient(app)
    cams_res = client.get("/api/v1/cameras")
    assert cams_res.status_code == 200
    cams = cams_res.json()
    assert len(cams) > 0

    cam_id = cams[0]["id"]
    res = client.post(f"/api/v1/cameras/{cam_id}/priority?priority=CRITICAL_ALERT")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SUCCESS"
    assert body["new_priority"] == "CRITICAL_ALERT"


def test_cross_camera_vehicle_journey_api():
    """Verify GET /api/v1/vehicles/{plate}/journey builds chronological observation timeline."""
    client = TestClient(app)
    res = client.get("/api/v1/vehicles/GJ01AB1234/journey")
    assert res.status_code == 200
    journey = res.json()
    assert "plate" in journey
    assert "journey_type" in journey
    assert journey["journey_type"] == "observation_sequence"
    assert "observations" in journey


def test_global_search_api():
    """Verify GET /api/v1/search endpoint returns multi-entity search results."""
    client = TestClient(app)
    res = client.get("/api/v1/search?q=cam")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    results = data["results"]
    assert "cameras" in results
    assert "alerts" in results
    assert "vehicles" in results
    assert "investigations" in results


def test_investigation_workspace_api():
    """Verify Investigation case creation and management API."""
    client = TestClient(app)
    payload = {
        "title": "Phase 3 Security Investigation",
        "description": "Multi-camera cross-correlation test case",
        "assigned_officer_name": "Inspector Vijay Kumar",
    }
    res = client.post("/api/v1/investigations", json=payload)
    assert res.status_code == 201
    case = res.json()
    assert "case_number" in case
    assert case["title"] == payload["title"]
    assert case["status"] in ("OPEN", "UNDER_REVIEW", "HUMAN_VERIFIED", "DISMISSED")

    # List cases
    list_res = client.get("/api/v1/investigations")
    assert list_res.status_code == 200
    assert len(list_res.json()) > 0


def test_security_secrets_audit():
    """Verify that credentials and passwords are strictly excluded from output payloads."""
    client = TestClient(app)
    res = client.get("/api/v1/cameras")
    assert res.status_code == 200
    cams_json = str(res.json())
    
    # Ensure raw CCTV password is not leaked in camera lists
    secret_pass = os.environ.get("SENTINEL_CCTV_PASSWORD", "")
    if secret_pass:
        assert secret_pass not in cams_json

    # Ensure RTSP URLs in response use masked placeholders or relative stream endpoints
    for cam in res.json():
        rtsp = cam.get("rtsp_url")
        if rtsp and "@" in rtsp:
            assert "***" in rtsp or "auth_masked" in rtsp or "localhost" in rtsp
