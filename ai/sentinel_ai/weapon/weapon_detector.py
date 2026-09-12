import logging
import time
from typing import Dict, List, Optional
import numpy as np

from ai.sentinel_ai.config.settings import ai_settings
from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent
from ai.sentinel_ai.scheduler.resource_manager import resource_manager
from ai.sentinel_ai.third_party.ai_surveillance_bridge import ai_bridge

logger = logging.getLogger("sentinel.ai.weapon_detector")


class WeaponDetector:
    """
    Weapon detection using third-party WeaponDetectionSystem or YOLO.
    Enforces multi-frame temporal confirmation:
    - Single frame detection -> POSSIBLE_WEAPON
    - Persisted N-frame detection -> WEAPON_DETECTED
    """

    def __init__(self, min_consecutive_frames: int = 5):
        self.model_name = "weapon_yolo"
        self.model_version = "1.0.0"
        self.min_consecutive_frames = min_consecutive_frames
        self.weapon_system = None
        self.frame_history: Dict[str, Dict] = {}  # track_id/key -> {count, bbox, last_seen}

        if ai_bridge.is_available("weapon"):
            try:
                WeaponClass = ai_bridge.get_module_class("weapon")
                self.weapon_system = WeaponClass()
                resource_manager.register_model(self.model_name, self.weapon_system, version=self.model_version)
                logger.info("WeaponDetector using third-party WeaponDetectionSystem")
            except Exception as e:
                logger.warning("Could not initialize third-party WeaponDetectionSystem: %s", e)

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "cam_default",
        track_id: Optional[str] = None,
    ) -> List[SentinelAIEvent]:
        if frame is None or frame.size == 0:
            return []

        start_time = time.time()
        events: List[SentinelAIEvent] = []

        try:
            candidates = []
            if self.weapon_system is not None and hasattr(self.weapon_system, "process_frame"):
                results = self.weapon_system.process_frame(frame)
                for res in results:
                    candidates.append({
                        "class_name": res.get("class") or res.get("label") or "weapon",
                        "confidence": float(res.get("confidence", 0.75)),
                        "bbox": res.get("bbox"),
                    })

            # Temporal voting per camera/track
            current_keys = set()
            for idx, cand in enumerate(candidates):
                key = f"{camera_id}_{track_id or idx}"
                current_keys.add(key)
                hist = self.frame_history.get(key, {"count": 0, "bbox": cand["bbox"]})
                hist["count"] += 1
                hist["bbox"] = cand["bbox"]
                self.frame_history[key] = hist

                conf = cand["confidence"]
                bbox = cand["bbox"]
                cls_name = cand["class_name"]

                if hist["count"] >= self.min_consecutive_frames:
                    # Confirmed weapon event
                    events.append(
                        SentinelAIEvent(
                            event_type=EventType.WEAPON_DETECTED,
                            camera_id=camera_id,
                            track_id=track_id,
                            class_name=f"Weapon Detected: {cls_name}",
                            confidence=round(conf, 4),
                            bounding_box=bbox,
                            model_name=self.model_name,
                            model_version=self.model_version,
                            status="CONFIRMED",
                            requires_human_review=True,
                            metadata={"consecutive_frames": hist["count"]},
                        )
                    )
                else:
                    # Possible weapon event
                    events.append(
                        SentinelAIEvent(
                            event_type=EventType.WEAPON_DETECTED,
                            camera_id=camera_id,
                            track_id=track_id,
                            class_name=f"Possible Weapon: {cls_name}",
                            confidence=round(conf, 4),
                            bounding_box=bbox,
                            model_name=self.model_name,
                            model_version=self.model_version,
                            status="POSSIBLE_WEAPON",
                            requires_human_review=True,
                            metadata={"consecutive_frames": hist["count"]},
                        )
                    )

            # Decay history for missing candidates
            for key in list(self.frame_history.keys()):
                if key.startswith(camera_id) and key not in current_keys:
                    self.frame_history[key]["count"] -= 1
                    if self.frame_history[key]["count"] <= 0:
                        del self.frame_history[key]

            latency_ms = (time.time() - start_time) * 1000.0
            resource_manager.record_inference(self.model_name, latency_ms, success=True)
        except Exception as e:
            logger.exception("Error in WeaponDetector inference: %s", e)
            resource_manager.record_inference(self.model_name, 0.0, success=False)

        return events
