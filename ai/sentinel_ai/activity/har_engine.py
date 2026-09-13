import logging
import time
from typing import Dict, List, Optional
import numpy as np

from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent
from ai.sentinel_ai.scheduler.resource_manager import resource_manager
from ai.sentinel_ai.third_party.ai_surveillance_bridge import ai_bridge

logger = logging.getLogger("sentinel.ai.har_engine")


class HAREngine:
    """
    Human Action Recognition (HAR) Engine integrating third-party SlowFast / action classifier.
    Labels supported: 'walking', 'running', 'falling', 'fighting', 'vandalism', 'normal'.
    Does NOT label normal activity as criminal.
    """

    def __init__(self):
        self.model_name = "har_slowfast"
        self.model_version = "1.0.0"
        self.har_system = None

        if ai_bridge.is_available("har"):
            try:
                HARClass = ai_bridge.get_module_class("har")
                self.har_system = HARClass()
                resource_manager.register_model(self.model_name, self.har_system, version=self.model_version)
                logger.info("HAREngine using third-party HumanActionRecognitionSystem")
            except Exception as e:
                logger.warning("Could not initialize third-party HAR system: %s", e)

    def process_frame_or_clip(
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
            if self.har_system is not None and hasattr(self.har_system, "process_frame"):
                results = self.har_system.process_frame(frame)
                for res in results:
                    activity_label = (res.get("action") or res.get("class") or "normal").lower()
                    conf = float(res.get("confidence", 0.70))

                    if activity_label in ("fight", "fighting", "vandalism", "falling"):
                        requires_review = True
                        status = "ANOMALOUS_ACTIVITY"
                    else:
                        requires_review = False
                        status = "NORMAL_ACTIVITY"

                    events.append(
                        SentinelAIEvent(
                            event_type=EventType.HUMAN_ACTIVITY_DETECTED,
                            camera_id=camera_id,
                            track_id=track_id,
                            class_name=activity_label.capitalize(),
                            confidence=round(conf, 4),
                            bounding_box=res.get("bbox"),
                            model_name=self.model_name,
                            model_version=self.model_version,
                            status=status,
                            requires_human_review=requires_review,
                            metadata={"activity": activity_label},
                        )
                    )

            latency_ms = (time.time() - start_time) * 1000.0
            resource_manager.record_inference(self.model_name, latency_ms, success=True)
        except Exception as e:
            logger.exception("Error in HAREngine inference: %s", e)
            resource_manager.record_inference(self.model_name, 0.0, success=False)

        return events
