import json
import logging
from typing import Any, List, Dict
from fastapi import WebSocket

logger = logging.getLogger("sentinel.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.alert_connections: List[WebSocket] = []
        self.event_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected to active pool. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.alert_connections:
            self.alert_connections.remove(websocket)
        if websocket in self.event_connections:
            self.event_connections.remove(websocket)
        logger.info("WebSocket client disconnected cleanly.")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Error sending personal message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)

    async def connect_alerts(self, websocket: WebSocket):
        await websocket.accept()
        if websocket not in self.alert_connections:
            self.alert_connections.append(websocket)
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        logger.info(f"Alert WebSocket client connected. Active alert listeners: {len(self.alert_connections)}")

    def disconnect_alerts(self, websocket: WebSocket):
        self.disconnect(websocket)

    async def connect_events(self, websocket: WebSocket):
        await websocket.accept()
        if websocket not in self.event_connections:
            self.event_connections.append(websocket)
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        logger.info(f"Event WebSocket client connected. Active event listeners: {len(self.event_connections)}")

    def disconnect_events(self, websocket: WebSocket):
        self.disconnect(websocket)

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        message = json.dumps({"type": "ALERT_CREATED", "event": "ALERT_CREATED", "alert": alert_data})
        logger.info(f"Broadcasting live alert: {alert_data.get('alert_code')} to {len(self.alert_connections)} listeners")
        dead = []
        for connection in self.alert_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect_alerts(conn)

    async def broadcast_event(self, event_data: Dict[str, Any]):
        message = json.dumps({"type": "AI_EVENT", "event": event_data})
        dead = []
        for connection in self.event_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect_events(conn)


ws_manager = ConnectionManager()
