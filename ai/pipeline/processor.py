from ai.detection.detector import ObjectDetector
from ai.tracking.tracker import ObjectTracker
from ai.anpr.plate_detector import PlateDetector
from ai.event_detection.event_engine import EventEngine
from ai.face_detection.detector import FaceDetector
import os


class StreamProcessor:
    """
    Complete end-to-end AI Stream Processing Pipeline.
    Frame Sampling -> Object Detection -> Tracking -> ANPR -> Event Classification
    """

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.5):
        self.detector = ObjectDetector(model_path or os.getenv("AI_MODEL_PATH", "yolo11n.pt"), confidence_threshold)
        self.tracker = ObjectTracker()
        self.anpr = PlateDetector()
        self.event_engine = EventEngine(
            confirmation_frames=int(os.getenv("AI_EVENT_CONFIRMATION_FRAMES", "3")),
            cooldown_seconds=int(os.getenv("AI_EVENT_COOLDOWN_SECONDS", "30")),
        )
        self.face_detector = FaceDetector(min_size=int(os.getenv("AI_FACE_MIN_SIZE", "40")))

    async def process_frame(self, camera_id: str, frame: any, pts_ms: float | None = None) -> dict:
        detections = await self.detector.detect(frame)
        if os.getenv("AI_FACE_DETECTION_ENABLED", "true").lower() == "true":
            detections.extend(await self.face_detector.detect(frame))
        tracked = await self.tracker.update(detections, pts_ms=pts_ms, camera_id=camera_id)

        # Vehicle ANPR processing
        for obj in tracked:
            obj_type = str(obj.get("object_type", "")).lower()
            if obj_type in {"car", "motorcycle", "bus", "truck", "vehicle"} and frame is not None:
                bbox = obj.get("bbox", {})
                x1, y1 = int(bbox.get("x1", 0)), int(bbox.get("y1", 0))
                x2, y2 = int(bbox.get("x2", 0)), int(bbox.get("y2", 0))
                if x2 > x1 and y2 > y1:
                    try:
                        vehicle_crop = frame[y1:y2, x1:x2]
                        anpr_res = await self.anpr.process_vehicle_crop(vehicle_crop)
                        if anpr_res and anpr_res.get("normalized_plate"):
                            obj["plate_number"] = anpr_res["plate_number"]
                            obj["normalized_plate"] = anpr_res["normalized_plate"]
                            obj["ocr_confidence"] = anpr_res["ocr_confidence"]
                    except Exception:
                        pass

        events = await self.event_engine.evaluate_observations(tracked, camera_id)
        
        return {
            "camera_id": camera_id,
            "detections": tracked,
            "events": events,
            "demo_mode": self.detector.demo_mode,
            "pts_ms": pts_ms,
        }
