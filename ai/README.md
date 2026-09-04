# Sentinel AI Worker

The AI worker is intentionally isolated from the API.

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

The initial worker contains interfaces only. Add the selected production-approved models during the AI implementation phase.
