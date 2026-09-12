"""
Multi-Camera AI Priority Scheduler for Sentinel Platform.

Manages processing slots across authorized CCTV cameras while respecting
GPU hardware constraints (NVIDIA RTX 4050 ~6 GB VRAM).
"""

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai.sentinel_ai.config.settings import ai_settings
from ai.sentinel_ai.scheduler.resource_manager import ModelResourceManager

logger = logging.getLogger("sentinel.ai.camera_scheduler")


class PriorityLevel(enum.IntEnum):
    CRITICAL_ALERT = 1
    ACTIVE_INVESTIGATION = 2
    WATCHLIST_CAMERA = 3
    USER_SELECTED_CAMERA = 4
    NORMAL_CAMERA = 5


@dataclass
class CameraHealthState:
    camera_id: str
    camera_code: str
    name: str
    priority: PriorityLevel = PriorityLevel.NORMAL_CAMERA
    connection_status: str = "DISCONNECTED"  # CONNECTED, CONNECTING, DISCONNECTED, ERROR
    ai_status: str = "IDLE"  # PROCESSING, ACTIVE, IDLE, ERROR, PAUSED
    last_frame_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    latency_ms: float = 0.0
    reconnect_count: int = 0
    next_reconnect_at: float = 0.0
    ai_error_count: int = 0
    total_frames_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CameraScheduler:
    """
    Schedules AI inference tasks across dynamic camera streams.
    Enforces GPU VRAM limits, sample intervals, priority queues, and reconnect backoffs.
    """

    def __init__(
        self,
        resource_manager: Optional[ModelResourceManager] = None,
        max_ai_cameras: Optional[int] = None,
        frame_sample_interval: Optional[int] = None,
        max_concurrent_inference: Optional[int] = None,
    ):
        self.resource_manager = resource_manager or ModelResourceManager()
        self.max_ai_cameras = max_ai_cameras or getattr(ai_settings, "MAX_AI_CAMERAS", 4)
        self.frame_sample_interval = frame_sample_interval or ai_settings.AI_FRAME_SAMPLE_INTERVAL
        self.max_concurrent_inference = max_concurrent_inference or getattr(ai_settings, "MAX_CONCURRENT_INFERENCE", 2)
        
        self.cameras: Dict[str, CameraHealthState] = {}
        self.active_slots: List[str] = []

    def register_camera(
        self,
        camera_id: str,
        camera_code: str,
        name: str,
        priority: PriorityLevel = PriorityLevel.NORMAL_CAMERA,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CameraHealthState:
        if camera_id in self.cameras:
            state = self.cameras[camera_id]
            state.name = name
            state.camera_code = camera_code
            state.priority = priority
            if metadata:
                state.metadata.update(metadata)
            return state

        state = CameraHealthState(
            camera_id=camera_id,
            camera_code=camera_code,
            name=name,
            priority=priority,
            last_heartbeat=time.time(),
            metadata=metadata or {},
        )
        self.cameras[camera_id] = state
        logger.info("Registered camera '%s' (%s) with priority %s", camera_code, camera_id, priority.name)
        self._rebalance_slots()
        return state

    def set_camera_priority(self, camera_id: str, priority: PriorityLevel) -> bool:
        if camera_id in self.cameras:
            old_prio = self.cameras[camera_id].priority
            self.cameras[camera_id].priority = priority
            logger.info("Updated camera '%s' priority from %s to %s", camera_id, old_prio.name, priority.name)
            self._rebalance_slots()
            return True
        return False

    def update_health(
        self,
        camera_id: str,
        connection_status: Optional[str] = None,
        ai_status: Optional[str] = None,
        latency_ms: Optional[float] = None,
        error: bool = False,
    ) -> None:
        if camera_id not in self.cameras:
            return
        state = self.cameras[camera_id]
        now = time.time()
        state.last_heartbeat = now
        if connection_status:
            state.connection_status = connection_status
        if ai_status:
            state.ai_status = ai_status
        if latency_ms is not None:
            state.latency_ms = latency_ms
        if error:
            state.ai_error_count += 1
            state.reconnect_count += 1
            # Exponential backoff: 2, 4, 8, ... max 60 seconds
            backoff_sec = min(60, 2 ** min(state.reconnect_count, 6))
            state.next_reconnect_at = now + backoff_sec
            state.connection_status = "ERROR"
            logger.warning(
                "Camera '%s' error logged. Reconnect backoff %ds (count=%d)",
                camera_id,
                backoff_sec,
                state.reconnect_count,
            )

    def should_process_frame(self, camera_id: str, frame_count: int) -> bool:
        if camera_id not in self.active_slots:
            return False
        state = self.cameras.get(camera_id)
        if not state:
            return False

        # Respect reconnect backoff delay if errored
        if state.connection_status == "ERROR" and time.time() < state.next_reconnect_at:
            return False

        # Frame sampling interval
        return (frame_count % self.frame_sample_interval) == 0

    def record_frame_processed(self, camera_id: str, latency_ms: float) -> None:
        if camera_id in self.cameras:
            state = self.cameras[camera_id]
            state.last_frame_at = time.time()
            state.total_frames_processed += 1
            state.latency_ms = latency_ms
            state.ai_status = "PROCESSING"
            state.connection_status = "CONNECTED"
            state.reconnect_count = 0

    def _rebalance_slots(self) -> None:
        """Assign active AI processing slots according to camera priority hierarchy."""
        sorted_cams = sorted(
            self.cameras.values(),
            key=lambda c: (c.priority.value, c.last_heartbeat or 0),
        )
        
        new_active = [c.camera_id for c in sorted_cams[: self.max_ai_cameras]]
        
        # Update AI status attributes
        for cam_id, cam in self.cameras.items():
            if cam_id in new_active:
                if cam.ai_status in ("IDLE", "PAUSED"):
                    cam.ai_status = "ACTIVE"
            else:
                cam.ai_status = "PAUSED"

        self.active_slots = new_active
        logger.debug("Active AI slots rebalanced: %s", self.active_slots)

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Return multi-camera scheduler telemetry for backend API."""
        now = time.time()
        cam_summaries = []
        for c in self.cameras.values():
            cam_summaries.append({
                "camera_id": c.camera_id,
                "camera_code": c.camera_code,
                "name": c.name,
                "priority": c.priority.name,
                "connection_status": c.connection_status,
                "ai_status": c.ai_status,
                "is_active_slot": c.camera_id in self.active_slots,
                "latency_ms": round(c.latency_ms, 2),
                "total_frames_processed": c.total_frames_processed,
                "reconnect_count": c.reconnect_count,
                "ai_error_count": c.ai_error_count,
                "last_seen_sec": round(now - c.last_heartbeat, 1) if c.last_heartbeat else None,
            })

        free_vram, total_vram = self.resource_manager.get_gpu_memory_mb()
        return {
            "total_registered_cameras": len(self.cameras),
            "max_ai_cameras": self.max_ai_cameras,
            "active_ai_cameras_count": len(self.active_slots),
            "frame_sample_interval": self.frame_sample_interval,
            "gpu_vram_free_mb": free_vram,
            "gpu_vram_total_mb": total_vram,
            "active_slots": self.active_slots,
            "cameras": cam_summaries,
        }


# Global instance
camera_scheduler = CameraScheduler()
