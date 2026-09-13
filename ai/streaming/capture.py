import asyncio
import logging
import math
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("sentinel.ai.capture")
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")


@dataclass(frozen=True)
class CapturedFrame:
    frame: Any
    pts_ms: float | None


class ReconnectBackoff:
    def __init__(self, initial: float = 2.0, maximum: float = 30.0):
        self.initial = initial
        self.maximum = maximum
        self.current = initial

    def failure_delay(self) -> float:
        delay = self.current
        self.current = min(self.current * 2, self.maximum)
        return delay

    def reset(self) -> None:
        self.current = self.initial


def sanitize_url_for_logging(url: str) -> str:
    """Masks credentials in RTSP/HTTP URLs for safe logging."""
    if "@" in url:
        try:
            scheme, rest = url.split("://", 1)
            user_pass, host_path = rest.split("@", 1)
            return f"{scheme}://***:***@{host_path}"
        except Exception:
            return "rtsp://***:***@stream"
    return url


class RtspCapture:
    def __init__(self, url: str):
        self.url = url
        self.capture = None

    async def open(self) -> bool:
        import cv2
        safe_url = sanitize_url_for_logging(self.url)
        logger.info("Opening RTSP TCP capture for %s", safe_url)
        self.capture = await asyncio.to_thread(cv2.VideoCapture, self.url, cv2.CAP_FFMPEG)
        return bool(self.capture and self.capture.isOpened())

    async def read(self) -> CapturedFrame | None:
        if not self.capture:
            return None
        import cv2
        ok, frame = await asyncio.to_thread(self.capture.read)
        if not ok:
            return None
        pts_ms = await asyncio.to_thread(self.capture.get, cv2.CAP_PROP_POS_MSEC)
        return CapturedFrame(frame=frame, pts_ms=float(pts_ms) if not math.isnan(float(pts_ms)) and pts_ms >= 0 else None)

    async def close(self) -> None:
        if self.capture is not None:
            await asyncio.to_thread(self.capture.release)
            self.capture = None