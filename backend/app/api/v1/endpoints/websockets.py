import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("sentinel.websocket")
router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await ws_manager.connect_alerts(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle heartbeat ping/pong
            if data == "ping" or '"ping"' in data.lower():
                await ws_manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect_alerts(websocket)
    except Exception as e:
        logger.warning(f"Alert WebSocket exception: {e}")
        ws_manager.disconnect_alerts(websocket)


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect_events(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping" or '"ping"' in data.lower():
                await ws_manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect_events(websocket)
    except Exception as e:
        logger.warning(f"Event WebSocket exception: {e}")
        ws_manager.disconnect_events(websocket)
