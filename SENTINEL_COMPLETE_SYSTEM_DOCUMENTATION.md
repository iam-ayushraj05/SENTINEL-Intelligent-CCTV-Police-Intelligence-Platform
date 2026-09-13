# SENTINEL Complete System Documentation

## 1. Executive Summary

SENTINEL is a unified CCTV intelligence and police command platform built around a modular FastAPI backend, a Next.js operations frontend, and an Ultralytics-powered AI detection pipeline. The platform is designed to ingest camera streams, detect persons/vehicles and suspicious events, correlate those events with watchlists and investigations, and generate operational alerts for police response teams.

This repository intentionally preserves a working platform architecture instead of replacing it with a mock or a single monolithic demo. The AI pipeline is grounded in the embedded Ultralytics implementation already present in the workspace, specifically the library at `ultralytics/ultralytics`.

## 2. Verified Technology Stack

### Backend
- FastAPI
- SQLAlchemy / async database layer
- Pydantic-based configuration and validation
- WebSocket-ready streaming and API endpoints
- SQLite by default for local dev, with production-ready migration paths for PostgreSQL/PostGIS deployments

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- dashboard, map, alerts, investigations, emergency, and camera monitoring modules

### AI Engine
- Ultralytics YOLO implementation embedded in the workspace under `ultralytics/`
- Verified library version: 8.4.142
- Detection models are loaded through `from ultralytics import YOLO` and inference is run via `model.predict(...)`
- Default default runtime model is configured as `yolo11n.pt`

## 3. Verified Ultralytics Facts

The repository includes the actual Ultralytics source tree, and the version is explicitly defined in [ultralytics/ultralytics/__init__.py](ultralytics/ultralytics/__init__.py):

- `__version__ = "8.4.142"`

The detection abstraction in [ai/detection/detector.py](ai/detection/detector.py) uses:

- `from ultralytics import YOLO`
- `self.model = YOLO(model_path)`
- `self.model.predict(source=frame, conf=self.confidence_threshold, verbose=False)`

This confirms the platform is using the real Ultralytics library, not a replacement detection engine.

The Ultralytics project supports multiple model families including YOLOv8, YOLO11, YOLO12, and YOLO26 according to the baked-in asset/model definitions in the upstream package. In practice, the platform configuration currently defaults to the lightweight `yolo11n.pt` path, which is consistent with a production-ready CCTV-first deployment profile.

## 4. Operational AI Pipeline

The canonical end-to-end flow is:

1. Camera or video source
2. Frame sampling and normalization
3. Ultralytics object detection (`YOLO.predict`)
4. Object tracking and event aggregation
5. Event engine scoring and confirmation logic
6. Alert generation and investigation workflow
7. Human verification, evidence capture, and response tracking

The implementation is defined in:

- [ai/detection/detector.py](ai/detection/detector.py)
- [ai/tracking/tracker.py](ai/tracking/tracker.py)
- [ai/pipeline/processor.py](ai/pipeline/processor.py)
- [ai/event_detection/event_engine.py](ai/event_detection/event_engine.py)

The stream processor wires the layers as:

- `ObjectDetector`
- `ObjectTracker`
- `PlateDetector`
- `EventEngine`

## 5. Default Configuration

The platform config lives in [backend/app/core/config.py](backend/app/core/config.py). Relevant defaults include:

- `ai_model: "yolov8n"`
- `ai_model_path: "yolo11n.pt"`
- `ai_confidence_threshold: 0.50`
- `ai_event_confirmation_frames: 3`
- `ai_event_cooldown_seconds: 30`

The AI worker layer also uses the env-driven model path in [ai/pipeline/processor.py](ai/pipeline/processor.py):

- `os.getenv("AI_MODEL_PATH", "yolo11n.pt")`

This means the deployed system supports custom validation and model override without breaking the default on-device detection path.

## 6. Data and Alert Flow

The platform includes full operational modules for:

- camera registry and health
- AI detection results
- watchlists and persons
- vehicle and ANPR workflows
- alerts and emergency response
- investigations and audit trails
- Google Drive evidence import and feed tracking

Key backend route and model files include:

- [backend/app/api/v1/router.py](backend/app/api/v1/router.py)
- [backend/app/models/camera.py](backend/app/models/camera.py)
- [backend/app/models/alert.py](backend/app/models/alert.py)
- [backend/app/models/person.py](backend/app/models/person.py)
- [backend/app/api/v1/endpoints/persons.py](backend/app/api/v1/endpoints/persons.py)
- [backend/app/api/v1/endpoints/feeds.py](backend/app/api/v1/endpoints/feeds.py)

## 7. Frontend Operational Views

The frontend has been built around real operational dashboards and map views. Relevant pages include:

- [frontend/app/emergency-cameras/page.tsx](frontend/app/emergency-cameras/page.tsx)
- [frontend/app/emergency/page.tsx](frontend/app/emergency/page.tsx)
- [frontend/components/map/MultiCameraMap.tsx](frontend/components/map/MultiCameraMap.tsx)
- [frontend/components/alerts/AIAlertPanel.tsx](frontend/components/alerts/AIAlertPanel.tsx)

These views rely on the shared API contracts in [frontend/lib/types.ts](frontend/lib/types.ts) and the mapped camera/alert model shapes.

## 8. Runtime and Deployment Commands

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Infrastructure

```bash
docker compose up -d postgres redis kafka mediamtx
```

## 9. Important Constraints and Production Notes

- The only approved CCTV AI detection engine for this project is the embedded Ultralytics source tree in the workspace.
- The system should not be switched to a different ML framework without explicit project-level approval.
- Model weights are typically downloaded at runtime when a model name like `yolo11n.pt` is requested, unless the file is already cached locally.
- The repository includes demo and synthetic data only. Real police feeds and sensitive operational data must remain behind secure access controls.

## 10. Verification Status

The implementation has been checked against the live workspace state:

- backend tests passed
- frontend production build passed
- the platform architecture remains cohesive and operational
- the AI detection chain is grounded in the actual Ultralytics implementation within the workspace

## 11. Conclusion

SENTINEL is a working, modular surveillance intelligence platform whose core AI layer is anchored to the actual Ultralytics package already embedded in the repository. The project is therefore aligned with the requirement to use the local Ultralytics codebase as the official CCTV detection engine while keeping the rest of the platform intact and production-oriented.
