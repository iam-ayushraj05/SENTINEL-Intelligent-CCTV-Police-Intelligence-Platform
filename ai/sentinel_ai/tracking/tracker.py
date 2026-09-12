import math
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np

logger = logging.getLogger("sentinel.ai.tracker")


class MultiObjectTracker:
    """
    Lightweight IoU/Centroid Tracker for maintaining track IDs per camera session.
    Prevents false cross-camera identity linkage.
    """

    def __init__(self, camera_id: str, iou_threshold: float = 0.3, max_disappeared: int = 15):
        self.camera_id = camera_id
        self.iou_threshold = iou_threshold
        self.max_disappeared = max_disappeared
        self.next_track_id = 1
        self.tracks: Dict[int, Dict] = {}  # track_id -> {bbox, disappeared, centroids}

    def _compute_iou(self, boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        denominator = float(boxAArea + boxBArea - interArea)
        if denominator <= 0:
            return 0.0
        return interArea / denominator

    def update(self, bboxes: List[List[float]]) -> Dict[int, int]:
        """
        Updates tracks with new frame bounding boxes [x1, y1, x2, y2].
        Returns map of box index in input list -> session track_id.
        """
        if not bboxes:
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]["disappeared"] += 1
                if self.tracks[track_id]["disappeared"] > self.max_disappeared:
                    del self.tracks[track_id]
            return {}

        index_to_track_id: Dict[int, int] = {}
        assigned_boxes = set()

        # Match existing tracks using IoU
        if self.tracks:
            track_ids = list(self.tracks.keys())
            for idx, box in enumerate(bboxes):
                best_iou = 0.0
                best_track_id = None
                for t_id in track_ids:
                    iou = self._compute_iou(box, self.tracks[t_id]["bbox"])
                    if iou > best_iou and iou >= self.iou_threshold:
                        best_iou = iou
                        best_track_id = t_id

                if best_track_id is not None and best_track_id not in index_to_track_id.values():
                    index_to_track_id[idx] = best_track_id
                    assigned_boxes.add(idx)
                    self.tracks[best_track_id]["bbox"] = box
                    self.tracks[best_track_id]["disappeared"] = 0

        # Mark unmatched tracks as disappeared
        for t_id, track_data in list(self.tracks.items()):
            if t_id not in index_to_track_id.values():
                track_data["disappeared"] += 1
                if track_data["disappeared"] > self.max_disappeared:
                    del self.tracks[t_id]

        # Assign new track IDs for new detections
        for idx, box in enumerate(bboxes):
            if idx not in assigned_boxes:
                new_id = self.next_track_id
                self.next_track_id += 1
                self.tracks[new_id] = {"bbox": box, "disappeared": 0}
                index_to_track_id[idx] = new_id

        return index_to_track_id
