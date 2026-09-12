import asyncio
import logging
import urllib.parse
from datetime import datetime
from typing import Any
import httpx
from app.core.config import settings

logger = logging.getLogger("sentinel.cctv_service")


def get_safe_rtsp_url(camera_id: str) -> str | None:
    """
    Builds RTSP URL for internal AI inference worker using backend environment credentials.
    Forces TCP via URL/capture flags. NEVER send this URL to browser.
    """
    if not settings.sentinel_cctv_email or not settings.sentinel_cctv_password:
        logger.warning("CCTV email/password credentials not set in environment settings")
        return None

    encoded_email = urllib.parse.quote(settings.sentinel_cctv_email, safe="")
    encoded_pass = urllib.parse.quote(settings.sentinel_cctv_password, safe="")
    host = settings.sentinel_cctv_host
    port = settings.sentinel_cctv_rtsp_port

    return f"rtsp://{encoded_email}:{encoded_pass}@{host}:{port}/stream/{camera_id}"


def get_safe_whep_url(camera_id: str) -> str | None:
    """
    Builds backend WHEP endpoint URL for low-latency WebRTC.
    """
    if not settings.sentinel_cctv_email or not settings.sentinel_cctv_password:
        return None

    encoded_email = urllib.parse.quote(settings.sentinel_cctv_email, safe="")
    encoded_pass = urllib.parse.quote(settings.sentinel_cctv_password, safe="")
    host = settings.sentinel_cctv_host
    port = settings.sentinel_cctv_whep_port

    return f"http://{encoded_email}:{encoded_pass}@{host}:{port}/stream/{camera_id}/whep"


def get_hls_url(camera_id: str) -> str:
    """
    Builds public CDN HLS stream URL for browser preview.
    """
    base = settings.sentinel_cctv_hls_base.rstrip("/")
    return f"{base}/{camera_id}/index.m3u8"


class CCTVService:
    @staticmethod
    async def fetch_remote_catalogue() -> list[dict[str, Any]]:
        """
        Fetches dynamic camera catalogue from https://cctv.corp8.cloud/cameras.json
        """
        url = settings.sentinel_cctv_catalogue_url
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    raw_records = data.get("cameras", data) if isinstance(data, dict) else data
                    if isinstance(raw_records, list):
                        return raw_records
                else:
                    logger.warning("CCTV catalogue endpoint returned status %d", response.status_code)
        except Exception as exc:
            logger.warning("Failed to fetch CCTV catalogue from %s: %s", url, exc)

        # Fallback to static cam01..cam30 list if remote catalogue is unreachable
        return [
            {
                "camera_id": f"cam{i:02d}",
                "name": f"CAM{i:02d}",
                "location": "Gujarat Range",
                "status": "online",
            }
            for i in range(1, 31)
        ]

    @staticmethod
    def normalize_camera_data(record: dict[str, Any]) -> dict[str, Any]:
        """
        Safely normalizes varied camera metadata schemas from cameras.json.
        """
        cam_id = str(record.get("id") or record.get("camera_id") or record.get("camera_code") or "").strip()
        name = str(record.get("name") or record.get("camera_name") or record.get("title") or f"CAM {cam_id}").strip()
        location = str(record.get("location") or record.get("zone") or record.get("district") or "Gujarat Range").strip()
        
        lat = record.get("latitude") or record.get("lat")
        lng = record.get("longitude") or record.get("lng") or record.get("lon")

        status = str(record.get("status") or "ONLINE").upper()

        return {
            "camera_code": cam_id,
            "name": name,
            "zone": location,
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lng) if lng is not None else None,
            "status": status,
            "hls_url": get_hls_url(cam_id),
            "has_rtsp": True,
            "has_whep": True,
            "ai_enabled": True,
            "anpr_enabled": True,
        }

    @staticmethod
    async def check_camera_health(camera_code: str) -> dict[str, Any]:
        """
        Checks real health of stream endpoint via TCP probe to RTSP port or HTTP check.
        """
        host = settings.sentinel_cctv_host
        port = settings.sentinel_cctv_rtsp_port
        start_time = asyncio.get_event_loop().time()
        
        try:
            # TCP connection check to RTSP port
            conn = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=3.0)
            writer.close()
            await writer.wait_closed()
            latency = (asyncio.get_event_loop().time() - start_time) * 1000.0
            return {
                "status": "ONLINE",
                "latency_ms": round(latency, 2),
                "checked_at": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.debug("Health check failed for %s: %s", camera_code, exc)
            return {
                "status": "OFFLINE",
                "latency_ms": None,
                "checked_at": datetime.utcnow().isoformat(),
                "error": "TCP stream connection timeout or refused",
            }
