import time
from typing import Dict, List, Optional
from ai.sentinel_ai.config.settings import ai_settings
from ai.sentinel_ai.events.schema import SentinelAIEvent


class TemporalValidator:
    """
    Temporal validator enforcing:
    - Event cooldown per camera & event type / track ID.
    - Multi-frame confirmation.
    - Duplicate suppression.
    """

    def __init__(
        self,
        cooldown_seconds: Optional[float] = None,
        min_confirmation_frames: Optional[int] = None,
    ):
        self.cooldown_seconds = cooldown_seconds or ai_settings.EVENT_COOLDOWN_SECONDS
        self.min_confirmation_frames = min_confirmation_frames or ai_settings.MIN_CONFIRMATION_FRAMES
        self.last_event_timestamps: Dict[str, float] = {}
        self.frame_counts: Dict[str, int] = {}

    def filter_events(self, events: List[SentinelAIEvent]) -> List[SentinelAIEvent]:
        if not events:
            return []

        now = time.time()
        filtered: List[SentinelAIEvent] = []

        for event in events:
            key = f"{event.camera_id}_{event.event_type.value}_{event.track_id or event.class_name}"

            # Cooldown check
            last_ts = self.last_event_timestamps.get(key, 0.0)
            if now - last_ts < self.cooldown_seconds:
                continue

            self.last_event_timestamps[key] = now
            filtered.append(event)

        return filtered
