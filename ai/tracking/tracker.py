from typing import Any


def _iou(left: dict[str, float], right: dict[str, float]) -> float:
    lx1, ly1, lx2, ly2 = left.get("x1", 0), left.get("y1", 0), left.get("x2", 0), left.get("y2", 0)
    rx1, ry1, rx2, ry2 = right.get("x1", 0), right.get("y1", 0), right.get("x2", 0), right.get("y2", 0)
    intersection = max(0, min(lx2, rx2) - max(lx1, rx1)) * max(0, min(ly2, ry2) - max(ly1, ry1))
    left_area = max(0, lx2 - lx1) * max(0, ly2 - ly1)
    right_area = max(0, rx2 - rx1) * max(0, ry2 - ry1)
    union = left_area + right_area - intersection
    return intersection / union if union else 0


class ObjectTracker:
    """
    ByteTrack / DeepSORT tracking abstraction.
    Assigns persistent tracking IDs across consecutive video frames.
    """

    def __init__(self):
        self.track_counter = 100
        self.active_tracks: dict[str, dict[str, Any]] = {}
        self.previous_pts_ms: float | None = None

    async def update(self, detections: list[dict[str, Any]], pts_ms: float | None = None, camera_id: str = "cam") -> list[dict[str, Any]]:
        if pts_ms is not None and self.previous_pts_ms is not None:
            delta_ms = pts_ms - self.previous_pts_ms
            if delta_ms < 0 or delta_ms > 10_000:
                self.active_tracks.clear()
        if pts_ms is not None:
            self.previous_pts_ms = pts_ms
        tracked = []
        matched: set[str] = set()
        prefix = camera_id.lower()
        for det in detections:
            det_copy = dict(det)
            candidates = [
                (track_id, track)
                for track_id, track in self.active_tracks.items()
                if track_id not in matched and track["object_type"] == det.get("object_type")
            ]
            best = max(candidates, key=lambda item: _iou(item[1]["bbox"], det.get("bbox", {})), default=None)
            if best and _iou(best[1]["bbox"], det.get("bbox", {})) >= 0.3:
                track_id = best[0]
                matched.add(track_id)
            else:
                self.track_counter += 1
                track_id = f"{prefix}-TRK-{self.track_counter}"
            det_copy["track_id"] = track_id
            if pts_ms is not None:
                det_copy["pts_ms"] = pts_ms
            self.active_tracks[track_id] = det_copy
            tracked.append(det_copy)
        active_ids = {item["track_id"] for item in tracked}
        self.active_tracks = {track_id: track for track_id, track in self.active_tracks.items() if track_id in matched or track_id in active_ids}
        return tracked
