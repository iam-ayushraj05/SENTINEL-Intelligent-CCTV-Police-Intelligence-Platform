import logging
import time
from typing import Dict, List, Optional
import numpy as np

from ai.sentinel_ai.activity.har_engine import HAREngine
from ai.sentinel_ai.anpr.detector import ANPRDetector
from ai.sentinel_ai.detectors.person_detector import PersonDetector
from ai.sentinel_ai.detectors.vehicle_detector import VehicleDetector
from ai.sentinel_ai.events.schema import SentinelAIEvent
from ai.sentinel_ai.face.face_engine import FaceEngine
from ai.sentinel_ai.tracking.tracker import MultiObjectTracker
from ai.sentinel_ai.validation.fire_smoke_validator import FireSmokeValidator
from ai.sentinel_ai.validation.temporal_validator import TemporalValidator
from ai.sentinel_ai.weapon.weapon_detector import WeaponDetector

logger = logging.getLogger("sentinel.ai.sentinel_adapter")


class SentinelAIAdapter:
    """
    Central AI Adapter unifying third-party AI engines into Sentinel platform events.
    Clean architectural boundary between Sentinel backend/streams and underlying models.
    """

    def __init__(self):
        self.person_detector = PersonDetector()
        self.vehicle_detector = VehicleDetector()
        self.anpr_detector = ANPRDetector()
        self.face_engine = FaceEngine()
        self.weapon_detector = WeaponDetector()
        self.har_engine = HAREngine()
        self.fire_smoke_validator = FireSmokeValidator()
        self.temporal_validator = TemporalValidator()
        self.trackers: Dict[str, MultiObjectTracker] = {}

    def get_tracker(self, camera_id: str) -> MultiObjectTracker:
        if camera_id not in self.trackers:
            self.trackers[camera_id] = MultiObjectTracker(camera_id=camera_id)
        return self.trackers[camera_id]

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "cam_default",
        enabled_capabilities: Optional[List[str]] = None,
    ) -> List[SentinelAIEvent]:
        if frame is None or frame.size == 0:
            return []

        if enabled_capabilities is None:
            enabled_capabilities = [
                "person",
                "vehicle",
                "anpr",
                "face",
                "weapon",
                "har",
                "fire_smoke",
            ]

        raw_events: List[SentinelAIEvent] = []
        tracker = self.get_tracker(camera_id)

        # 1. Person Detection
        if "person" in enabled_capabilities:
            p_events = self.person_detector.detect(frame, camera_id=camera_id)
            raw_events.extend(p_events)

        # 2. Vehicle Detection
        if "vehicle" in enabled_capabilities:
            v_events = self.vehicle_detector.detect(frame, camera_id=camera_id)
            raw_events.extend(v_events)

        # Update Multi-Object Tracker with bboxes from detections
        all_bboxes = [evt.bounding_box for evt in raw_events if evt.bounding_box]
        track_map = tracker.update(all_bboxes)

        # Assign track IDs back to raw events
        bbox_idx = 0
        for evt in raw_events:
            if evt.bounding_box:
                t_id = track_map.get(bbox_idx)
                if t_id:
                    evt.track_id = f"tr_{t_id}"
                bbox_idx += 1

        # 3. ANPR Detection
        if "anpr" in enabled_capabilities:
            anpr_events = self.anpr_detector.process_crop_or_frame(frame, camera_id=camera_id)
            raw_events.extend(anpr_events)

        # 4. Face Recognition / Detection
        if "face" in enabled_capabilities:
            face_events = self.face_engine.process_frame(frame, camera_id=camera_id)
            raw_events.extend(face_events)

        # 5. Weapon Detection
        if "weapon" in enabled_capabilities:
            w_events = self.weapon_detector.process_frame(frame, camera_id=camera_id)
            raw_events.extend(w_events)

        # 6. Human Action Recognition (HAR)
        if "har" in enabled_capabilities:
            har_events = self.har_engine.process_frame_or_clip(frame, camera_id=camera_id)
            raw_events.extend(har_events)

        # 7. Fire & Smoke Validation
        if "fire_smoke" in enabled_capabilities:
            fs_events = self.fire_smoke_validator.process_frame(frame, camera_id=camera_id)
            raw_events.extend(fs_events)

        # Filter events via Temporal Validator (cooldown & duplicate suppression)
        filtered_events = self.temporal_validator.filter_events(raw_events)
        return filtered_events


sentinel_ai_adapter = SentinelAIAdapter()
