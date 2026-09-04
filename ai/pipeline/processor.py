from ai.detection.detector import ObjectDetector
from ai.tracking.tracker import ObjectTracker
from ai.anpr.plate_detector import PlateDetector
from ai.event_detection.event_engine import EventEngine


class StreamProcessor:
    """
    Complete end-to-end AI Stream Processing Pipeline.
    Frame Sampling -> Object Detection -> Tracking -> ANPR -> Event Classification
    """

    def __init__(self):
        self.detector = ObjectDetector()
        self.tracker = ObjectTracker()
        self.anpr = PlateDetector()
        self.event_engine = EventEngine()

    async def process_frame(self, camera_id: str, frame: any) -> dict:
        detections = await self.detector.detect(frame)
        tracked = await self.tracker.update(detections)
        events = await self.event_engine.evaluate_observations(tracked)
        
        return {
            "camera_id": camera_id,
            "detections": tracked,
            "events": events,
            "demo_mode": True,
        }
