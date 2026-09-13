import logging
import time
from typing import Any, Dict, List, Optional
import numpy as np

from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent
from ai.sentinel_ai.scheduler.resource_manager import resource_manager
from ai.sentinel_ai.third_party.ai_surveillance_bridge import ai_bridge

logger = logging.getLogger("sentinel.ai.face_engine")


class FaceEngine:
    """
    Facial Detection and Identification Engine.
    Crucial distinction:
    - FACE_DETECTED: standard face detection (not an identity match).
    - FACE_MATCH: identity match against database/watchlist. ALWAYS requires human verification.
    """

    def __init__(self, match_threshold: float = 0.65):
        self.model_name = "face_insightface"
        self.model_version = "1.0.0"
        self.match_threshold = match_threshold
        self.facial_system = None

        if ai_bridge.is_available("face"):
            try:
                FacialClass = ai_bridge.get_module_class("face")
                self.facial_system = FacialClass()
                resource_manager.register_model(self.model_name, self.facial_system, version=self.model_version)
                logger.info("FaceEngine using third-party FacialRecognitionSystem")
            except Exception as e:
                logger.warning("Could not initialize third-party FacialRecognitionSystem: %s", e)

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
            if self.facial_system is not None and hasattr(self.facial_system, "process_frame"):
                results = self.facial_system.process_frame(frame)
                for res in results:
                    bbox = res.get("bbox")
                    conf = float(res.get("confidence", 0.85))
                    person_name = res.get("name") or res.get("person_id")
                    match_score = float(res.get("match_confidence", 0.0))

                    if person_name and match_score >= self.match_threshold:
                        # FACE_MATCH event
                        events.append(
                            SentinelAIEvent(
                                event_type=EventType.FACE_MATCH,
                                camera_id=camera_id,
                                track_id=track_id,
                                class_name=f"Face Match: {person_name}",
                                confidence=round(match_score, 4),
                                bounding_box=bbox,
                                model_name=self.model_name,
                                model_version=self.model_version,
                                status="MATCH_PROPOSED",
                                requires_human_review=True,  # STRICT REQUIREMENT
                                metadata={
                                    "matched_name": person_name,
                                    "match_confidence": match_score,
                                    "detection_confidence": conf,
                                    "demographics": res.get("demographics", {}),
                                },
                            )
                        )
                    else:
                        # Standard FACE_DETECTED event
                        events.append(
                            SentinelAIEvent(
                                event_type=EventType.FACE_DETECTED,
                                camera_id=camera_id,
                                track_id=track_id,
                                class_name="Face detected",
                                confidence=round(conf, 4),
                                bounding_box=bbox,
                                model_name=self.model_name,
                                model_version=self.model_version,
                                status="DETECTED",
                                requires_human_review=False,
                                metadata={"demographics": res.get("demographics", {})},
                            )
                        )

            latency_ms = (time.time() - start_time) * 1000.0
            resource_manager.record_inference(self.model_name, latency_ms, success=True)
        except Exception as e:
            logger.exception("Error in FaceEngine inference: %s", e)
            resource_manager.record_inference(self.model_name, 0.0, success=False)

        return events
