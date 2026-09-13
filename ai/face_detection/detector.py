import asyncio
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("sentinel.ai.face_detector")


class FaceDetector:
    """OpenCV face detector used by the live camera pipeline.

    This detects faces and returns locations only. Identity matching must be
    performed by the configured recognition service and is never inferred here.
    """

    def __init__(self, min_size: int = 40):
        self.min_size = min_size
        self.classifier = None
        self.net = None
        try:
            import cv2
            cascade_path = os.getenv(
                "AI_FACE_CASCADE_PATH",
                str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"),
            )
            classifier = cv2.CascadeClassifier(cascade_path) if Path(cascade_path).is_file() else None
            if classifier is not None and not classifier.empty():
                self.classifier = classifier
            else:
                model_dir = Path(os.getenv(
                    "AI_FACE_MODEL_DIR",
                    str(Path(__file__).resolve().parents[2] / "face-recognition-using-deep-learning" / "face_detection_model"),
                ))
                proto = model_dir / "deploy.prototxt"
                weights = model_dir / "res10_300x300_ssd_iter_140000.caffemodel"
                if proto.exists() and weights.exists():
                    self.net = cv2.dnn.readNetFromCaffe(str(proto), str(weights))
                else:
                    logger.warning("No OpenCV face model was found")
        except ImportError:
            logger.warning("OpenCV is not installed; face detection is unavailable")
        except Exception:
            logger.exception("Failed to initialize the OpenCV face detector")

    async def detect(self, frame: Any) -> list[dict[str, Any]]:
        if frame is None or (self.classifier is None and self.net is None):
            return []
        try:
            shape = getattr(frame, "shape", ())
            if len(shape) != 3 or shape[0] <= 0 or shape[1] <= 0:
                return []
            return await asyncio.to_thread(self._detect, frame)
        except Exception:
            logger.exception("Face detection failed for an input frame")
            return []

    def _detect(self, frame: Any) -> list[dict[str, Any]]:
        import cv2

        if self.classifier is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(self.min_size, self.min_size))
            candidates = [(x, y, width, height, 0.0) for x, y, width, height in faces]
        else:
            height, width = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            self.net.setInput(blob)
            raw = self.net.forward()
            candidates = []
            for index in range(raw.shape[2]):
                confidence = float(raw[0, 0, index, 2])
                if confidence < 0.5:
                    continue
                x1, y1, x2, y2 = raw[0, 0, index, 3:7] * [width, height, width, height]
                candidates.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1), confidence))
        results = []
        for index, (x, y, width, height, confidence) in enumerate(candidates):
            results.append({
                "object_type": "face",
                "confidence": round(confidence, 4),
                "bbox": {"x1": float(x), "y1": float(y), "x2": float(x + width), "y2": float(y + height)},
                "track_id": f"face-{index}",
                "event_type": None,
                "metadata": {"detector": "opencv-haar" if self.classifier is not None else "opencv-ssd-caffe", "identity_status": "UNMATCHED"},
            })
        return results