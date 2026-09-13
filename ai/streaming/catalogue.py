from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class CameraStream:
    camera_id: str
    name: str
    rtsp_url: str | None
    webrtc_url: str | None
    hls_url: str | None
    status: str | None
    metadata: dict[str, Any]


class CameraCatalogue:
    def __init__(self, url: str, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout

    async def fetch(self) -> list[CameraStream]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            payload = response.json()
        records = payload.get("cameras", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("Camera catalogue must be a list or an object containing cameras")
        return [self._normalize(record) for record in records if isinstance(record, dict)]

    @staticmethod
    def _normalize(record: dict[str, Any]) -> CameraStream:
        import os
        import urllib.parse
        camera_id = str(record.get("id") or record.get("camera_id") or record.get("camera_code") or "").strip()
        if not camera_id:
            raise ValueError("Camera catalogue record is missing an id")

        email = os.environ.get("SENTINEL_CCTV_EMAIL", "")
        password = os.environ.get("SENTINEL_CCTV_PASSWORD", "")
        host = os.environ.get("SENTINEL_CCTV_HOST", "103.250.160.189")
        rtsp_port = os.environ.get("SENTINEL_CCTV_RTSP_PORT", "8554")
        whep_port = os.environ.get("SENTINEL_CCTV_WHEP_PORT", "8889")
        hls_base = os.environ.get("SENTINEL_CCTV_HLS_BASE", "https://cctv.corp8.cloud").rstrip("/")

        rtsp_url = record.get("rtsp_url") or record.get("rtsp")
        if not rtsp_url and email and password:
            encoded_email = urllib.parse.quote(email, safe="")
            encoded_pass = urllib.parse.quote(password, safe="")
            rtsp_url = f"rtsp://{encoded_email}:{encoded_pass}@{host}:{rtsp_port}/stream/{camera_id}"

        webrtc_url = record.get("webrtc_url") or record.get("whep_url") or record.get("whep")
        if not webrtc_url and email and password:
            encoded_email = urllib.parse.quote(email, safe="")
            encoded_pass = urllib.parse.quote(password, safe="")
            webrtc_url = f"http://{encoded_email}:{encoded_pass}@{host}:{whep_port}/stream/{camera_id}/whep"

        hls_url = record.get("hls_url") or record.get("hls") or f"{hls_base}/{camera_id}/index.m3u8"

        return CameraStream(
            camera_id=camera_id,
            name=str(record.get("name", record.get("camera_name", camera_id))),
            rtsp_url=rtsp_url,
            webrtc_url=webrtc_url,
            hls_url=hls_url,
            status=record.get("status", "online"),
            metadata=record,
        )

    async def get(self, camera_id: str | None = None) -> CameraStream:
        cameras = await self.fetch()
        if not cameras:
            raise RuntimeError("Camera catalogue is empty")
        if camera_id:
            for camera in cameras:
                if camera.camera_id == camera_id:
                    return camera
            raise RuntimeError(f"Camera {camera_id} is not present in the catalogue")
        for camera in cameras:
            if camera.rtsp_url:
                return camera
        raise RuntimeError("Camera catalogue has no RTSP source")