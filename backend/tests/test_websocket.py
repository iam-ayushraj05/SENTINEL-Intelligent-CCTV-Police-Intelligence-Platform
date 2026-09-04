import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.websocket_manager import ws_manager


def test_websocket_alerts_connection_and_heartbeat():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/alerts") as websocket:
        # Test heartbeat ping/pong
        websocket.send_text("ping")
        data = websocket.receive_text()
        parsed = json.loads(data)
        assert parsed["type"] == "pong"


@pytest.mark.asyncio
async def test_websocket_alert_broadcast():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/alerts") as websocket:
        # Broadcast test alert
        test_alert = {
            "id": "test-alert-123",
            "alert_code": "ALT-2026-TEST",
            "alert_type": "WATCHLIST_MATCH",
            "severity": "CRITICAL",
            "title": "Test Watchlist Alert",
            "confidence": 0.98,
        }
        await ws_manager.broadcast_alert(test_alert)
        data = websocket.receive_text()
        parsed = json.loads(data)
        assert parsed["type"] == "ALERT_CREATED"
        assert parsed["alert"]["alert_code"] == "ALT-2026-TEST"
