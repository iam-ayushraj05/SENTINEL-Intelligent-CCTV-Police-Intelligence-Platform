"""
Camera Stream Manager — connection lifecycle, health monitoring, and reconnect logic.

Wraps RtspCapture with session management, metrics, and exponential backoff.
Designed for backend AI processing only; NEVER exposes RTSP credentials.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

logger = logging.getLogger("sentinel.stream_manager")


@dataclass
class StreamMetrics:
    """Connection metrics for a single camera stream — no secrets."""
    camera_id: str
    state: str = "IDLE"  # IDLE | CONNECTING | LIVE | RECONNECTING | ERROR | STOPPED
    connected_at: float | None = None
    disconnected_at: float | None = None
    last_heartbeat: float | None = None
    last_frame_pts_ms: float | None = None
    reconnect_count: int = 0
    total_frames: int = 0
    last_error: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def uptime_seconds(self) -> float | None:
        if self.connected_at is None:
            return None
        end = self.disconnected_at or time.monotonic()
        return round(end - self.connected_at, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "session_id": self.session_id,
            "state": self.state,
            "uptime_seconds": self.uptime_seconds,
            "reconnect_count": self.reconnect_count,
            "total_frames": self.total_frames,
            "last_error": self.last_error,
            "last_heartbeat": self.last_heartbeat,
        }


class ReconnectPolicy:
    """Exponential backoff with jitter: 2→4→8→16→30s cap."""

    def __init__(
        self,
        initial: float = 2.0,
        maximum: float = 30.0,
        jitter_factor: float = 0.25,
        max_retries: int = 50,
    ):
        self.initial = initial
        self.maximum = maximum
        self.jitter_factor = jitter_factor
        self.max_retries = max_retries
        self._current = initial
        self._attempt = 0

    def next_delay(self) -> float | None:
        """Returns next delay in seconds, or None if max retries exceeded."""
        self._attempt += 1
        if 0 < self.max_retries < self._attempt:
            return None
        import random
        jitter = 1.0 + (random.random() * 2 - 1) * self.jitter_factor
        delay = min(self._current * jitter, self.maximum)
        self._current = min(self._current * 2, self.maximum)
        return delay

    def reset(self) -> None:
        self._current = self.initial
        self._attempt = 0


class CameraStreamManager:
    """
    Manages connection lifecycle for a single camera stream.

    Responsibilities:
    - Connect to authorized camera (RTSP TCP)
    - Monitor connection with heartbeat timestamps
    - Reconnect with exponential backoff (never tight-loop)
    - Release stream resources on disconnect
    - Track connection metrics
    """

    def __init__(self, camera_id: str, stable_threshold_seconds: float = 10.0):
        self.camera_id = camera_id
        self.stable_threshold = stable_threshold_seconds
        self.metrics = StreamMetrics(camera_id=camera_id)
        self._policy = ReconnectPolicy()
        self._capture = None
        self._stopped = False
        self._stable_since: float | None = None

    async def connect(self) -> bool:
        """Attempt to open the RTSP stream. Returns True on success."""
        from app.services.cctv_service import get_safe_rtsp_url

        rtsp_url = get_safe_rtsp_url(self.camera_id)
        if not rtsp_url:
            self.metrics.state = "ERROR"
            self.metrics.last_error = "CCTV credentials not configured"
            logger.warning("Cannot connect camera %s: credentials missing", self.camera_id)
            return False

        self.metrics.state = "CONNECTING"
        logger.info("Connecting to camera %s...", self.camera_id)

        try:
            from ai.streaming.capture import RtspCapture
            self._capture = RtspCapture(rtsp_url)
            opened = await self._capture.open()
            if opened:
                self.metrics.state = "LIVE"
                self.metrics.connected_at = time.monotonic()
                self.metrics.disconnected_at = None
                self.metrics.last_heartbeat = time.monotonic()
                self._stable_since = time.monotonic()
                self._policy.reset()
                logger.info("Camera %s connected successfully (session %s)", self.camera_id, self.metrics.session_id)
                return True
            else:
                self.metrics.state = "ERROR"
                self.metrics.last_error = "RTSP stream could not be opened"
                await self._release_capture()
                return False
        except Exception as exc:
            self.metrics.state = "ERROR"
            self.metrics.last_error = str(exc)[:200]
            logger.warning("Camera %s connection failed: %s", self.camera_id, exc)
            await self._release_capture()
            return False

    async def read_frame(self):
        """Read a single frame. Returns CapturedFrame or None."""
        if self._capture is None:
            return None

        try:
            frame = await self._capture.read()
            if frame is not None:
                self.metrics.total_frames += 1
                self.metrics.last_heartbeat = time.monotonic()
                self.metrics.last_frame_pts_ms = frame.pts_ms

                # Reset backoff after stable playback
                if (self._stable_since is not None and
                        time.monotonic() - self._stable_since >= self.stable_threshold):
                    self._policy.reset()
                    self._stable_since = None  # Only reset once per stable period

                return frame
            else:
                # Stream ended / disconnected
                self.metrics.state = "RECONNECTING"
                self.metrics.disconnected_at = time.monotonic()
                self._stable_since = None
                await self._release_capture()
                return None
        except Exception as exc:
            self.metrics.state = "ERROR"
            self.metrics.last_error = str(exc)[:200]
            self._stable_since = None
            await self._release_capture()
            return None

    async def reconnect_with_backoff(self) -> bool:
        """Wait according to backoff policy, then attempt reconnection."""
        if self._stopped:
            return False

        delay = self._policy.next_delay()
        if delay is None:
            self.metrics.state = "STOPPED"
            self.metrics.last_error = "Max reconnection attempts exceeded"
            logger.error("Camera %s: max retries exceeded, stopping", self.camera_id)
            return False

        self.metrics.state = "RECONNECTING"
        self.metrics.reconnect_count += 1
        logger.info("Camera %s: reconnecting in %.1fs (attempt %d)", self.camera_id, delay, self.metrics.reconnect_count)

        await asyncio.sleep(delay)

        if self._stopped:
            return False

        return await self.connect()

    async def stop(self) -> None:
        """Stop the stream and release all resources."""
        self._stopped = True
        self.metrics.state = "STOPPED"
        self.metrics.disconnected_at = time.monotonic()
        await self._release_capture()
        logger.info("Camera %s stream stopped (session %s)", self.camera_id, self.metrics.session_id)

    async def _release_capture(self) -> None:
        """Release the underlying capture resources."""
        if self._capture is not None:
            try:
                await self._capture.close()
            except Exception:
                pass
            self._capture = None

    @property
    def is_live(self) -> bool:
        return self.metrics.state == "LIVE" and self._capture is not None

    @property
    def is_stopped(self) -> bool:
        return self._stopped
