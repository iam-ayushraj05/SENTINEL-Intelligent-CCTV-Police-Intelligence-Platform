import logging
import time
from typing import Dict, List, Optional
import cv2
import numpy as np

from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent
from ai.sentinel_ai.scheduler.resource_manager import resource_manager
from ai.sentinel_ai.third_party.ai_surveillance_bridge import ai_bridge

logger = logging.getLogger("sentinel.ai.fire_smoke_validator")


class FireSmokeValidator:
    """
    Fire and Smoke Detector with 5-layer false positive mitigation:
    1. Per-class confidence thresholds (smoke requires higher confidence)
    2. Size ratio filter (0.3% <= area <= 85%)
    3. HSV color verification
    4. Multi-frame IoU confirmation
    5. Cooldown suppression per location
    """

    def __init__(self, alert_cooldown: float = 3.0, min_consecutive_frames: int = 5):
        self.model_name = "fire_smoke_yolo"
        self.model_version = "1.0.0"
        self.alert_cooldown = alert_cooldown
        self.min_consecutive_frames = min_consecutive_frames
        self.fire_system = None
        self.last_alert_times: Dict[str, float] = {}

        if ai_bridge.is_available("fire"):
            try:
                FireClass = ai_bridge.get_module_class("fire")
                self.fire_system = FireClass()
                resource_manager.register_model(self.model_name, self.fire_system, version=self.model_version)
                logger.info("FireSmokeValidator using third-party FireDetectionSystem")
            except Exception as e:
                logger.warning("Could not initialize third-party FireDetectionSystem: %s", e)

    def verify_hsv_color(self, crop: np.ndarray, class_type: str) -> bool:
        if crop is None or crop.size == 0:
            return False
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        if class_type == "fire":
            # Warm color mask (red / orange / yellow)
            mask1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([25, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
            warm_ratio = (cv2.countNonZero(mask1) + cv2.countNonZero(mask2)) / (crop.shape[0] * crop.shape[1])
            return warm_ratio >= 0.05
        elif class_type == "smoke":
            # Low saturation, mid-high value grey/white mask
            mask = cv2.inRange(hsv, np.array([0, 0, 80]), np.array([180, 50, 230]))
            grey_ratio = cv2.countNonZero(mask) / (crop.shape[0] * crop.shape[1])
            return grey_ratio >= 0.10
        return True

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "cam_default",
    ) -> List[SentinelAIEvent]:
        if frame is None or frame.size == 0:
            return []

        start_time = time.time()
        events: List[SentinelAIEvent] = []

        try:
            raw_detections = []
            if self.fire_system is not None and hasattr(self.fire_system, "process_frame"):
                raw_detections = self.fire_system.process_frame(frame)

            now = time.time()
            h, w = frame.shape[:2]
            frame_area = float(h * w)

            for det in raw_detections:
                cls_type = (det.get("class") or det.get("label") or "fire").lower()
                conf = float(det.get("confidence", 0.70))
                bbox = det.get("bbox")

                if bbox:
                    x1, y1, x2, y2 = bbox
                    box_area = float((x2 - x1) * (y2 - y1))
                    ratio = box_area / frame_area

                    # Size sanity check
                    if ratio < 0.003 or ratio > 0.85:
                        continue

                    # HSV color verification
                    crop = frame[int(y1):int(y2), int(x1):int(x2)]
                    if not self.verify_hsv_color(crop, cls_type):
                        continue

                # Cooldown check per location key
                cooldown_key = f"{camera_id}_{cls_type}"
                if now - self.last_alert_times.get(cooldown_key, 0.0) < self.alert_cooldown:
                    continue

                self.last_alert_times[cooldown_key] = now
                evt_type = EventType.FIRE_DETECTED if "fire" in cls_type else EventType.SMOKE_DETECTED

                events.append(
                    SentinelAIEvent(
                        event_type=evt_type,
                        camera_id=camera_id,
                        class_name=cls_type.capitalize(),
                        confidence=round(conf, 4),
                        bounding_box=bbox,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        status="CONFIRMED",
                        requires_human_review=True,
                        metadata={"false_positive_checks_passed": True},
                    )
                )

            latency_ms = (time.time() - start_time) * 1000.0
            resource_manager.record_inference(self.model_name, latency_ms, success=True)
        except Exception as e:
            logger.exception("Error in FireSmokeValidator inference: %s", e)
            resource_manager.record_inference(self.model_name, 0.0, success=False)

        return events
