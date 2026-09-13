from collections import defaultdict, deque
from time import monotonic
from typing import Any


def _iou(left: dict[str, float], right: dict[str, float]) -> float:
    lx1, ly1, lx2, ly2 = left.get("x1", 0), left.get("y1", 0), left.get("x2", 0), left.get("y2", 0)
    rx1, ry1, rx2, ry2 = right.get("x1", 0), right.get("y1", 0), right.get("x2", 0), right.get("y2", 0)
    intersection = max(0, min(lx2, rx2) - max(lx1, rx1)) * max(0, min(ly2, ry2) - max(ly1, ry1))
    union = max(0, lx2 - lx1) * max(0, ly2 - ly1) + max(0, rx2 - rx1) * max(0, ry2 - ry1) - intersection
    return intersection / union if union else 0


class EventEngine:
    """
    Evaluates tracking trajectories, loitering time, crowd density, and line-crossing to classify events.
    """

    def __init__(self, confirmation_frames: int = 3, cooldown_seconds: int = 30):
        self.confirmation_frames = confirmation_frames
        self.cooldown_seconds = cooldown_seconds
        self.history: dict[tuple[str, str], deque[float]] = defaultdict(lambda: deque(maxlen=20))
        self.last_emitted: dict[tuple[str, str], float] = {}

    async def evaluate_observations(self, tracked_objects: list[dict[str, Any]], camera_id: str = "unknown") -> list[dict[str, Any]]:
        events = []
        persons = [item for item in tracked_objects if str(item.get("object_type", "")).lower() == "person"]
        for obj in tracked_objects:
            object_type = str(obj.get("object_type", "")).lower()
            base_event = "PERSON_DETECTED" if object_type == "person" else "VEHICLE_DETECTED" if object_type in {"car", "motorcycle", "truck", "bus", "vehicle"} else None
            if base_event:
                events.extend(self._immediate_event(camera_id, base_event, obj))

            if object_type in {"gun", "firearm", "pistol", "rifle", "weapon"}:
                events.extend(self._immediate_event(camera_id, "GUN_DETECTED", obj))
                if any(_iou(person.get("bbox", {}), obj.get("bbox", {})) > 0.01 for person in persons):
                    events.extend(self._immediate_event(camera_id, "PERSON_HOLDING_GUN", obj))

            if obj.get("normalized_plate"):
                events.extend(self._immediate_event(camera_id, "ANPR_PLATE_DETECTED", obj))

            event_type = obj.get("event_type") or obj.get("behavior")
            if event_type:
                events.extend(self._confirmed_event(camera_id, str(event_type).upper(), obj))
        return events

    def _immediate_event(self, camera_id: str, event_type: str, obj: dict[str, Any]) -> list[dict[str, Any]]:
        key = (camera_id, f"{event_type}:{obj.get('track_id', 'scene')}")
        now = monotonic()
        if now - self.last_emitted.get(key, 0) < self.cooldown_seconds:
            return []
        self.last_emitted[key] = now
        return [self._event(event_type, obj)]

    def _confirmed_event(self, camera_id: str, event_type: str, obj: dict[str, Any]) -> list[dict[str, Any]]:
        key = (camera_id, f"{event_type}:{obj.get('track_id', 'scene')}")
        now = monotonic()
        self.history[key].append(now)
        if len(self.history[key]) < self.confirmation_frames:
            return []
        if now - self.last_emitted.get(key, 0) < self.cooldown_seconds:
            return []
        self.last_emitted[key] = now
        return [self._event(event_type, obj)]

    @staticmethod
    def _event(event_type: str, obj: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "object_type": obj.get("object_type"),
            "confidence": obj.get("confidence", 0),
            "track_id": obj.get("track_id"),
            "metadata": obj.get("metadata", {}),
        }
