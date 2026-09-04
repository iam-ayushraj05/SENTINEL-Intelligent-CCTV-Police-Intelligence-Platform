from abc import ABC, abstractmethod
import uuid
from datetime import datetime


class VMSAdapter(ABC):
    @abstractmethod
    async def authenticate(self) -> bool:
        pass

    @abstractmethod
    async def get_cameras(self) -> list[dict]:
        pass

    @abstractmethod
    async def get_stream(self, camera_id: str) -> dict:
        pass

    @abstractmethod
    async def get_camera_health(self, camera_id: str) -> dict:
        pass


class MockVMSAdapter(VMSAdapter):
    def __init__(self, vendor_name: str = "Sentinel-VMS-Gateway"):
        self.vendor_name = vendor_name

    async def authenticate(self) -> bool:
        return True

    async def get_cameras(self) -> list[dict]:
        return [
            {
                "camera_code": "CAM-GJ-000127",
                "name": "Ring Road Junction",
                "zone": "Ahmedabad South",
                "latitude": 23.0225,
                "longitude": 72.5714,
                "status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/cam01",
            },
            {
                "camera_code": "CAM-GJ-000128",
                "name": "SG Highway Express Gate 4",
                "zone": "Ahmedabad North",
                "latitude": 23.0900,
                "longitude": 72.5342,
                "status": "ONLINE",
                "rtsp_url": "rtsp://localhost:8554/cam02",
            },
        ]

    async def get_stream(self, camera_id: str) -> dict:
        return {
            "camera_id": camera_id,
            "protocol": "WEBRTC",
            "session_url": f"http://localhost:8889/live/{camera_id}",
            "hls_url": f"http://localhost:8888/live/{camera_id}/index.m3u8",
            "webrtc_url": f"http://localhost:8889/live/{camera_id}",
            "status": "STREAMING",
        }

    async def get_camera_health(self, camera_id: str) -> dict:
        return {
            "camera_id": camera_id,
            "status": "ONLINE",
            "latency_ms": 42.5,
            "fps": 25.0,
            "checked_at": datetime.utcnow().isoformat(),
        }
