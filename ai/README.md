# Sentinel AI Worker

The AI worker is isolated from the API process but publishes normalized detections
and confirmed events to the existing FastAPI ingestion endpoint.

Planned pipeline:

```text
RTSP/WebRTC frame
→ frame sampler
→ object detector
→ tracker
→ plate detector
→ OCR
→ normalization
→ confidence fusion
→ event publisher
```

Runtime requirements:

- `AI_MODEL_PATH`: Ultralytics checkpoint path, for example `yolo11n.pt` or an approved custom event model.
- `AI_CAMERA_ID`: UUID of the camera being processed.
- `AI_STREAM_URL`: RTSP/WebRTC-compatible source readable by OpenCV.
- `SENTINEL_API_URL`: FastAPI base URL, default `http://localhost:8000/api/v1`.
- `AI_EVENT_CONFIRMATION_FRAMES`: temporal confirmation count, default `3`.
- `AI_EVENT_COOLDOWN_SECONDS`: duplicate-event cooldown, default `30`.

The worker requires `ultralytics`, `opencv-python-headless`, and `httpx`. The
bundled `ultralytics/` repository is used as the source implementation; review
its AGPL obligations before production deployment.
