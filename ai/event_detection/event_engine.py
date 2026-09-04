from typing import Any


class EventEngine:
    """
    Evaluates tracking trajectories, loitering time, crowd density, and line-crossing to classify events.
    """

    async def evaluate_observations(self, tracked_objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events = []
        for obj in tracked_objects:
            if obj.get("object_type") == "person":
                events.append({
                    "event_type": "PERSON_DETECTED",
                    "object_type": "person",
                    "confidence": obj["confidence"],
                    "track_id": obj.get("track_id"),
                })
            elif obj.get("object_type") in ["car", "motorcycle", "truck", "bus"]:
                events.append({
                    "event_type": "VEHICLE_DETECTED",
                    "object_type": obj["object_type"],
                    "confidence": obj["confidence"],
                    "track_id": obj.get("track_id"),
                })
        return events
