import os
from pydantic import BaseModel


class AISettings(BaseModel):
    AI_DEVICE: str = os.getenv("AI_DEVICE", "auto")
    AI_MAX_CONCURRENT_MODELS: int = int(os.getenv("AI_MAX_CONCURRENT_MODELS", "2"))
    AI_FRAME_SAMPLE_INTERVAL: int = int(os.getenv("AI_FRAME_SAMPLE_INTERVAL", "2"))
    AI_MAX_GPU_MEMORY_MB: int = int(os.getenv("AI_MAX_GPU_MEMORY_MB", "5000"))
    AI_DETECTION_CONFIDENCE: float = float(os.getenv("AI_DETECTION_CONFIDENCE", "0.45"))
    TEMPORAL_WINDOW: int = int(os.getenv("TEMPORAL_WINDOW", "10"))
    MIN_CONFIRMATION_FRAMES: int = int(os.getenv("MIN_CONFIRMATION_FRAMES", "5"))
    EVENT_COOLDOWN_SECONDS: float = float(os.getenv("EVENT_COOLDOWN_SECONDS", "3.0"))


ai_settings = AISettings()
